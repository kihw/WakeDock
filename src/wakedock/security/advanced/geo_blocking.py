"""
Geographic Blocking Manager

Provides geographic-based access control including:
- Country-level blocking/allowing
- Real-time geolocation lookup
- Custom geographic rules
- Exception handling for VPNs/proxies
"""

import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from wakedock.database import get_db_session
from wakedock.security.advanced.models import (
    SecurityRule, SecurityEvent, GeoBlock, SecurityRuleType,
    SecurityActionType, ThreatLevel
)
from wakedock.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class GeoLocation:
    """Geographic location information"""
    ip_address: str
    country_code: str
    country_name: str
    region: str
    city: str
    latitude: float
    longitude: float
    timezone: str
    isp: str
    is_proxy: bool
    is_vpn: bool
    threat_score: float


@dataclass
class GeoRule:
    """Geographic blocking rule"""
    id: int
    country_code: str
    country_name: str
    block_type: str  # deny, allow, monitor
    organization_id: Optional[int]
    is_active: bool
    exceptions: List[str]  # IP ranges to exclude


class GeoBlockingManager:
    """Manages geographic access control"""
    
    def __init__(self):
        self.settings = get_settings()
        self._geo_cache: Dict[str, GeoLocation] = {}
        self._cache_ttl = 3600  # 1 hour
        self._blocked_countries: Dict[str, Set[str]] = {}  # org_id -> country_codes
        self._allowed_countries: Dict[str, Set[str]] = {}  # org_id -> country_codes
        self._last_rules_update = datetime.min
        self._session: Optional[aiohttp.ClientSession] = None
        self._monitoring_task = None
        
        # GeoIP service configuration
        self.geoip_services = [
            {
                "name": "ip-api.com",
                "url": "http://ip-api.com/json/{ip}",
                "fields": "status,message,country,countryCode,region,regionName,city,lat,lon,timezone,isp,proxy",
                "rate_limit": 45,  # requests per minute
                "free": True
            },
            {
                "name": "ipgeolocation.io", 
                "url": "https://api.ipgeolocation.io/ipgeo?apiKey={api_key}&ip={ip}",
                "rate_limit": 1000,  # per month for free tier
                "free": False  # requires API key
            }
        ]
        
    async def start_monitoring(self):
        """Start geo blocking monitoring"""
        if self._monitoring_task is None:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Geo blocking monitoring started")
    
    async def stop_monitoring(self):
        """Stop geo blocking monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
        
        if self._session:
            await self._session.close()
            self._session = None
            
        logger.info("Geo blocking monitoring stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await self._update_rules_cache()
                await self._cleanup_old_cache_entries()
                await asyncio.sleep(300)  # Check every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Geo blocking monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _update_rules_cache(self):
        """Update geographic rules cache"""
        if (datetime.utcnow() - self._last_rules_update).total_seconds() < 300:  # 5 minutes
            return
        
        try:
            async with get_db_session() as session:
                geo_blocks = await session.query(GeoBlock).filter(
                    GeoBlock.is_active == True
                ).all()
                
                # Clear and rebuild cache
                self._blocked_countries.clear()
                self._allowed_countries.clear()
                
                for block in geo_blocks:
                    org_key = str(block.organization_id) if block.organization_id else "global"
                    
                    if block.block_type == "deny":
                        if org_key not in self._blocked_countries:
                            self._blocked_countries[org_key] = set()
                        self._blocked_countries[org_key].add(block.country_code.upper())
                    
                    elif block.block_type == "allow":
                        if org_key not in self._allowed_countries:
                            self._allowed_countries[org_key] = set()
                        self._allowed_countries[org_key].add(block.country_code.upper())
                
                self._last_rules_update = datetime.utcnow()
                logger.debug(f"Updated geo rules cache with {len(geo_blocks)} rules")
                
        except Exception as e:
            logger.error(f"Failed to update geo rules cache: {e}")
    
    async def _cleanup_old_cache_entries(self):
        """Remove old GeoIP cache entries"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self._cache_ttl)
        
        to_remove = []
        for ip, location in self._geo_cache.items():
            # Check if cached entry is too old (we don't store timestamps in GeoLocation currently)
            # This is a simplified cleanup - in production you'd store cache timestamps
            if len(self._geo_cache) > 1000:  # Arbitrary limit
                to_remove.append(ip)
        
        for ip in to_remove[:100]:  # Remove up to 100 old entries
            del self._geo_cache[ip]
        
        if to_remove:
            logger.debug(f"Cleaned up {len(to_remove[:100])} old geo cache entries")
    
    async def get_geo_location(self, ip_address: str, use_cache: bool = True) -> Optional[GeoLocation]:
        """Get geographic location for IP address"""
        
        # Check cache first
        if use_cache and ip_address in self._geo_cache:
            return self._geo_cache[ip_address]
        
        # Skip private/local IPs
        try:
            import ipaddress
            ip = ipaddress.ip_address(ip_address)
            if ip.is_private or ip.is_loopback or ip.is_reserved:
                location = GeoLocation(
                    ip_address=ip_address,
                    country_code="XX",
                    country_name="Private/Local",
                    region="N/A",
                    city="N/A",
                    latitude=0.0,
                    longitude=0.0,
                    timezone="UTC",
                    isp="Local",
                    is_proxy=False,
                    is_vpn=False,
                    threat_score=0.0
                )
                self._geo_cache[ip_address] = location
                return location
        except ValueError:
            return None
        
        # Query external GeoIP service
        location = await self._query_geoip_service(ip_address)
        if location and use_cache:
            self._geo_cache[ip_address] = location
        
        return location
    
    async def _query_geoip_service(self, ip_address: str) -> Optional[GeoLocation]:
        """Query external GeoIP service"""
        if not self._session:
            return None
        
        # Try the first available service (ip-api.com for free tier)
        service = self.geoip_services[0]
        
        try:
            url = service["url"].format(ip=ip_address)
            async with self._session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("status") == "success":
                        return GeoLocation(
                            ip_address=ip_address,
                            country_code=data.get("countryCode", "XX"),
                            country_name=data.get("country", "Unknown"),
                            region=data.get("regionName", "Unknown"),
                            city=data.get("city", "Unknown"),
                            latitude=float(data.get("lat", 0.0)),
                            longitude=float(data.get("lon", 0.0)),
                            timezone=data.get("timezone", "UTC"),
                            isp=data.get("isp", "Unknown"),
                            is_proxy=data.get("proxy", False),
                            is_vpn=False,  # Would need additional service for VPN detection
                            threat_score=0.0  # Would be calculated based on various factors
                        )
                    else:
                        logger.warning(f"GeoIP lookup failed for {ip_address}: {data.get('message', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"GeoIP service error for {ip_address}: {e}")
        
        return None
    
    async def is_country_blocked(self, country_code: str, organization_id: Optional[int] = None) -> bool:
        """Check if country is blocked"""
        await self._update_rules_cache()
        
        country_code = country_code.upper()
        
        # Check organization-specific blocks
        if organization_id:
            org_key = str(organization_id)
            if org_key in self._blocked_countries and country_code in self._blocked_countries[org_key]:
                return True
        
        # Check global blocks
        if "global" in self._blocked_countries and country_code in self._blocked_countries["global"]:
            return True
        
        return False
    
    async def is_country_allowed(self, country_code: str, organization_id: Optional[int] = None) -> bool:
        """Check if country is explicitly allowed"""
        await self._update_rules_cache()
        
        country_code = country_code.upper()
        
        # Check organization-specific allows
        if organization_id:
            org_key = str(organization_id)
            if org_key in self._allowed_countries and country_code in self._allowed_countries[org_key]:
                return True
        
        # Check global allows
        if "global" in self._allowed_countries and country_code in self._allowed_countries["global"]:
            return True
        
        return False
    
    async def should_block_ip(self, ip_address: str, organization_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """Determine if IP should be blocked based on geographic rules"""
        
        location = await self.get_geo_location(ip_address)
        if not location:
            return False, "Unable to determine location"
        
        country_code = location.country_code
        
        # Check if country is explicitly allowed (takes precedence)
        if await self.is_country_allowed(country_code, organization_id):
            return False, f"Country {country_code} is explicitly allowed"
        
        # Check if country is blocked
        if await self.is_country_blocked(country_code, organization_id):
            return True, f"Country {country_code} is blocked"
        
        # Additional checks for suspicious characteristics
        if location.is_proxy or location.is_vpn:
            if location.threat_score > 50.0:
                return True, f"High-risk proxy/VPN from {country_code}"
        
        return False, None
    
    async def add_country_block(
        self,
        country_code: str,
        block_type: str,
        user_id: int,
        organization_id: Optional[int] = None,
        country_name: Optional[str] = None,
        exceptions: Optional[List[str]] = None
    ) -> GeoBlock:
        """Add a country to the block/allow list"""
        
        country_code = country_code.upper()
        if len(country_code) != 2:
            raise ValueError("Country code must be a 2-letter ISO code")
        
        if block_type not in ["deny", "allow", "monitor"]:
            raise ValueError("Block type must be 'deny', 'allow', or 'monitor'")
        
        async with get_db_session() as session:
            # Check for existing rule
            existing = await session.query(GeoBlock).filter(
                GeoBlock.country_code == country_code,
                GeoBlock.organization_id == organization_id,
                GeoBlock.is_active == True
            ).first()
            
            if existing:
                # Update existing rule
                existing.block_type = block_type
                existing.exceptions = exceptions or []
                existing.updated_at = datetime.utcnow()
                geo_block = existing
            else:
                # Create new rule
                geo_block = GeoBlock(
                    country_code=country_code,
                    country_name=country_name or country_code,
                    block_type=block_type,
                    organization_id=organization_id,
                    created_by_user_id=user_id,
                    exceptions=exceptions or []
                )
                session.add(geo_block)
            
            await session.commit()
            await session.refresh(geo_block)
            
            # Clear cache to force refresh
            self._last_rules_update = datetime.min
            
            logger.info(f"Added geo block rule: {country_code} -> {block_type} by user {user_id}")
            return geo_block
    
    async def remove_country_block(self, block_id: int, user_id: int) -> bool:
        """Remove a country block rule"""
        async with get_db_session() as session:
            geo_block = await session.query(GeoBlock).filter(
                GeoBlock.id == block_id
            ).first()
            
            if not geo_block:
                return False
            
            geo_block.is_active = False
            await session.commit()
            
            # Clear cache to force refresh
            self._last_rules_update = datetime.min
            
            logger.info(f"Removed geo block rule {block_id}: {geo_block.country_code} by user {user_id}")
            return True
    
    async def get_country_rules(self, organization_id: Optional[int] = None) -> List[GeoRule]:
        """Get all active country rules"""
        async with get_db_session() as session:
            query = session.query(GeoBlock).filter(
                GeoBlock.is_active == True
            )
            
            if organization_id:
                query = query.filter(GeoBlock.organization_id == organization_id)
            
            blocks = await query.all()
            
            return [
                GeoRule(
                    id=block.id,
                    country_code=block.country_code,
                    country_name=block.country_name,
                    block_type=block.block_type,
                    organization_id=block.organization_id,
                    is_active=block.is_active,
                    exceptions=block.exceptions
                )
                for block in blocks
            ]
    
    async def log_geo_event(
        self,
        ip_address: str,
        country_code: str,
        action_taken: str,
        reason: str,
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> SecurityEvent:
        """Log a geographic security event"""
        
        async with get_db_session() as session:
            event = SecurityEvent(
                event_type="geo_blocking",
                threat_level=ThreatLevel.MEDIUM if action_taken == "blocked" else ThreatLevel.LOW,
                title=f"Geographic Access Control: {action_taken}",
                description=f"IP {ip_address} from {country_code}: {reason}",
                source_ip=ip_address,
                country_code=country_code,
                organization_id=organization_id,
                user_id=user_id,
                blocked=(action_taken == "blocked"),
                event_metadata={
                    "action": action_taken,
                    "reason": reason,
                    "country_code": country_code
                }
            )
            
            session.add(event)
            await session.commit()
            await session.refresh(event)
            
            logger.info(f"Logged geo event: {action_taken} for {ip_address} from {country_code}")
            return event
    
    async def get_country_statistics(self, organization_id: Optional[int] = None) -> Dict[str, Dict]:
        """Get statistics about country-based access"""
        async with get_db_session() as session:
            # Get security events for geographic blocking
            query = session.query(SecurityEvent).filter(
                SecurityEvent.event_type == "geo_blocking"
            )
            
            if organization_id:
                query = query.filter(SecurityEvent.organization_id == organization_id)
            
            # Last 30 days
            since_date = datetime.utcnow() - timedelta(days=30)
            events = await query.filter(SecurityEvent.timestamp >= since_date).all()
            
            stats = {}
            for event in events:
                country = event.country_code or "Unknown"
                if country not in stats:
                    stats[country] = {
                        "total_requests": 0,
                        "blocked_requests": 0,
                        "allowed_requests": 0,
                        "last_activity": None
                    }
                
                stats[country]["total_requests"] += 1
                if event.blocked:
                    stats[country]["blocked_requests"] += 1
                else:
                    stats[country]["allowed_requests"] += 1
                
                if not stats[country]["last_activity"] or event.timestamp > stats[country]["last_activity"]:
                    stats[country]["last_activity"] = event.timestamp
            
            return stats


# Global instance
_geo_blocking_manager: Optional[GeoBlockingManager] = None


def get_geo_blocking_manager() -> GeoBlockingManager:
    """Get geo blocking manager instance"""
    global _geo_blocking_manager
    if _geo_blocking_manager is None:
        _geo_blocking_manager = GeoBlockingManager()
    return _geo_blocking_manager


async def initialize_geo_blocking_manager() -> GeoBlockingManager:
    """Initialize and start geo blocking manager"""
    manager = get_geo_blocking_manager()
    await manager.start_monitoring()
    return manager