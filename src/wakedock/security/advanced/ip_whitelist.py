"""
IP Whitelisting Manager

Provides IP address whitelisting and blacklisting functionality including:
- Dynamic IP range management
- Organization-specific rules
- Automatic threat detection
- Real-time blocking and allowlisting
"""

import logging
import ipaddress
import asyncio
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from wakedock.database import get_db_session
from wakedock.database.models import User
from wakedock.security.advanced.models import (
    SecurityRule, SecurityEvent, IPWhitelist, SecurityRuleType, 
    SecurityActionType, ThreatLevel
)
from wakedock.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class IPAnalysis:
    """IP address analysis result"""
    ip_address: str
    is_whitelisted: bool
    is_blacklisted: bool
    country_code: Optional[str]
    reputation_score: float  # 0-100, higher is better
    risk_factors: List[str]
    recommendations: List[str]


@dataclass
class IPWhitelistRule:
    """IP whitelist rule"""
    id: int
    ip_range: str
    label: str
    organization_id: Optional[int]
    expires_at: Optional[datetime]
    is_active: bool


class IPWhitelistManager:
    """Manages IP whitelisting and blacklisting"""
    
    def __init__(self):
        self.settings = get_settings()
        self._whitelist_cache: Dict[str, Set[ipaddress.IPv4Network]] = {}
        self._blacklist_cache: Dict[str, Set[ipaddress.IPv4Network]] = {}
        self._cache_ttl = 300  # 5 minutes
        self._last_cache_update = datetime.min
        self._monitoring_task = None
        
    async def start_monitoring(self):
        """Start IP monitoring background task"""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("IP whitelist monitoring started")
    
    async def stop_monitoring(self):
        """Stop IP monitoring background task"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
            logger.info("IP whitelist monitoring stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await self._update_cache()
                await self._cleanup_expired_rules()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"IP monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def _update_cache(self):
        """Update IP whitelist/blacklist cache"""
        if (datetime.utcnow() - self._last_cache_update).total_seconds() < self._cache_ttl:
            return
        
        try:
            async with get_db_session() as session:
                # Update whitelist cache
                whitelist_rules = await session.query(SecurityRule).filter(
                    SecurityRule.rule_type == SecurityRuleType.IP_WHITELIST,
                    SecurityRule.is_active == True
                ).all()
                
                blacklist_rules = await session.query(SecurityRule).filter(
                    SecurityRule.rule_type == SecurityRuleType.IP_BLACKLIST,
                    SecurityRule.is_active == True
                ).all()
                
                # Clear and rebuild cache
                self._whitelist_cache.clear()
                self._blacklist_cache.clear()
                
                for rule in whitelist_rules:
                    org_key = str(rule.organization_id) if rule.organization_id else "global"
                    if org_key not in self._whitelist_cache:
                        self._whitelist_cache[org_key] = set()
                    
                    for ip_range in rule.conditions.get("ip_ranges", []):
                        try:
                            network = ipaddress.ip_network(ip_range, strict=False)
                            self._whitelist_cache[org_key].add(network)
                        except ValueError as e:
                            logger.warning(f"Invalid IP range in whitelist rule {rule.id}: {ip_range} - {e}")
                
                for rule in blacklist_rules:
                    org_key = str(rule.organization_id) if rule.organization_id else "global"
                    if org_key not in self._blacklist_cache:
                        self._blacklist_cache[org_key] = set()
                    
                    for ip_range in rule.conditions.get("ip_ranges", []):
                        try:
                            network = ipaddress.ip_network(ip_range, strict=False)
                            self._blacklist_cache[org_key].add(network)
                        except ValueError as e:
                            logger.warning(f"Invalid IP range in blacklist rule {rule.id}: {ip_range} - {e}")
                
                self._last_cache_update = datetime.utcnow()
                logger.debug(f"Updated IP cache with {len(whitelist_rules)} whitelist and {len(blacklist_rules)} blacklist rules")
                
        except Exception as e:
            logger.error(f"Failed to update IP cache: {e}")
    
    async def _cleanup_expired_rules(self):
        """Clean up expired IP rules"""
        try:
            async with get_db_session() as session:
                # Find expired whitelist entries
                expired_entries = await session.query(IPWhitelist).filter(
                    IPWhitelist.expires_at.isnot(None),
                    IPWhitelist.expires_at < datetime.utcnow(),
                    IPWhitelist.is_active == True
                ).all()
                
                for entry in expired_entries:
                    entry.is_active = False
                    logger.info(f"Deactivated expired IP whitelist entry: {entry.ip_range}")
                
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired IP rules: {e}")
    
    async def is_ip_whitelisted(self, ip_address: str, organization_id: Optional[int] = None) -> bool:
        """Check if IP address is whitelisted"""
        await self._update_cache()
        
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Check organization-specific whitelist first
            if organization_id:
                org_key = str(organization_id)
                if org_key in self._whitelist_cache:
                    for network in self._whitelist_cache[org_key]:
                        if ip in network:
                            return True
            
            # Check global whitelist
            if "global" in self._whitelist_cache:
                for network in self._whitelist_cache["global"]:
                    if ip in network:
                        return True
            
            return False
            
        except ValueError:
            logger.warning(f"Invalid IP address format: {ip_address}")
            return False
    
    async def is_ip_blacklisted(self, ip_address: str, organization_id: Optional[int] = None) -> bool:
        """Check if IP address is blacklisted"""
        await self._update_cache()
        
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Check organization-specific blacklist first
            if organization_id:
                org_key = str(organization_id)
                if org_key in self._blacklist_cache:
                    for network in self._blacklist_cache[org_key]:
                        if ip in network:
                            return True
            
            # Check global blacklist
            if "global" in self._blacklist_cache:
                for network in self._blacklist_cache["global"]:
                    if ip in network:
                        return True
            
            return False
            
        except ValueError:
            logger.warning(f"Invalid IP address format: {ip_address}")
            return False
    
    async def add_whitelist_entry(
        self,
        ip_range: str,
        label: str,
        user_id: int,
        organization_id: Optional[int] = None,
        description: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> IPWhitelist:
        """Add IP address or range to whitelist"""
        
        # Validate IP range
        try:
            ipaddress.ip_network(ip_range, strict=False)
        except ValueError as e:
            raise ValueError(f"Invalid IP range format: {ip_range} - {e}")
        
        async with get_db_session() as session:
            # Check for existing entry
            existing = await session.query(IPWhitelist).filter(
                IPWhitelist.ip_range == ip_range,
                IPWhitelist.organization_id == organization_id,
                IPWhitelist.is_active == True
            ).first()
            
            if existing:
                raise ValueError(f"IP range {ip_range} is already whitelisted")
            
            entry = IPWhitelist(
                ip_range=ip_range,
                label=label,
                description=description,
                organization_id=organization_id,
                created_by_user_id=user_id,
                expires_at=expires_at
            )
            
            session.add(entry)
            await session.commit()
            await session.refresh(entry)
            
            # Create corresponding security rule
            await self._create_whitelist_rule(entry, user_id)
            
            # Clear cache to force refresh
            self._last_cache_update = datetime.min
            
            logger.info(f"Added IP whitelist entry: {ip_range} by user {user_id}")
            return entry
    
    async def _create_whitelist_rule(self, whitelist_entry: IPWhitelist, user_id: int):
        """Create security rule for whitelist entry"""
        async with get_db_session() as session:
            rule = SecurityRule(
                name=f"IP Whitelist: {whitelist_entry.label}",
                description=f"Auto-generated whitelist rule for {whitelist_entry.ip_range}",
                rule_type=SecurityRuleType.IP_WHITELIST,
                conditions={
                    "ip_ranges": [whitelist_entry.ip_range]
                },
                action=SecurityActionType.ALLOW,
                organization_id=whitelist_entry.organization_id,
                created_by_user_id=user_id
            )
            
            session.add(rule)
            await session.commit()
    
    async def remove_whitelist_entry(self, entry_id: int, user_id: int) -> bool:
        """Remove IP whitelist entry"""
        async with get_db_session() as session:
            entry = await session.query(IPWhitelist).filter(
                IPWhitelist.id == entry_id
            ).first()
            
            if not entry:
                return False
            
            entry.is_active = False
            
            # Also deactivate corresponding security rule
            rule = await session.query(SecurityRule).filter(
                SecurityRule.rule_type == SecurityRuleType.IP_WHITELIST,
                SecurityRule.conditions.contains({"ip_ranges": [entry.ip_range]})
            ).first()
            
            if rule:
                rule.is_active = False
            
            await session.commit()
            
            # Clear cache to force refresh
            self._last_cache_update = datetime.min
            
            logger.info(f"Removed IP whitelist entry {entry_id}: {entry.ip_range} by user {user_id}")
            return True
    
    async def get_whitelist_entries(self, organization_id: Optional[int] = None) -> List[IPWhitelistRule]:
        """Get all active whitelist entries"""
        async with get_db_session() as session:
            query = session.query(IPWhitelist).filter(
                IPWhitelist.is_active == True
            )
            
            if organization_id:
                query = query.filter(IPWhitelist.organization_id == organization_id)
            
            entries = await query.all()
            
            return [
                IPWhitelistRule(
                    id=entry.id,
                    ip_range=entry.ip_range,
                    label=entry.label,
                    organization_id=entry.organization_id,
                    expires_at=entry.expires_at,
                    is_active=entry.is_active
                )
                for entry in entries
            ]
    
    async def analyze_ip(self, ip_address: str, organization_id: Optional[int] = None) -> IPAnalysis:
        """Analyze IP address for security threats"""
        
        is_whitelisted = await self.is_ip_whitelisted(ip_address, organization_id)
        is_blacklisted = await self.is_ip_blacklisted(ip_address, organization_id)
        
        # Basic analysis (can be extended with external threat intelligence)
        risk_factors = []
        recommendations = []
        reputation_score = 50.0  # Neutral
        
        if is_whitelisted:
            reputation_score = 90.0
            recommendations.append("IP is whitelisted - trusted source")
        elif is_blacklisted:
            reputation_score = 10.0
            risk_factors.append("IP is blacklisted")
            recommendations.append("Block all requests from this IP")
        
        # Check for private/reserved ranges
        try:
            ip = ipaddress.ip_address(ip_address)
            if ip.is_private:
                risk_factors.append("Private IP address")
                reputation_score += 20.0
            elif ip.is_loopback:
                risk_factors.append("Loopback address")
                reputation_score += 30.0
            elif ip.is_reserved:
                risk_factors.append("Reserved IP address")
                recommendations.append("Investigate unusual reserved IP usage")
        except ValueError:
            risk_factors.append("Invalid IP format")
            reputation_score = 0.0
        
        # Get country information (placeholder - would integrate with GeoIP service)
        country_code = None  # Would be populated by geo service
        
        return IPAnalysis(
            ip_address=ip_address,
            is_whitelisted=is_whitelisted,
            is_blacklisted=is_blacklisted,
            country_code=country_code,
            reputation_score=min(100.0, max(0.0, reputation_score)),
            risk_factors=risk_factors,
            recommendations=recommendations
        )
    
    async def create_dynamic_rule(
        self,
        ip_address: str,
        action: SecurityActionType,
        duration_seconds: int,
        reason: str,
        user_id: int,
        organization_id: Optional[int] = None
    ) -> SecurityRule:
        """Create a temporary dynamic security rule"""
        
        async with get_db_session() as session:
            rule = SecurityRule(
                name=f"Dynamic Rule: {action.value} {ip_address}",
                description=f"Temporary rule: {reason}",
                rule_type=SecurityRuleType.IP_BLACKLIST if action in [SecurityActionType.DENY, SecurityActionType.BLOCK_TEMPORARY] else SecurityRuleType.IP_WHITELIST,
                conditions={
                    "ip_ranges": [f"{ip_address}/32"]
                },
                action=action,
                action_config={
                    "block_duration": duration_seconds,
                    "auto_created": True,
                    "reason": reason
                },
                organization_id=organization_id,
                created_by_user_id=user_id
            )
            
            session.add(rule)
            await session.commit()
            await session.refresh(rule)
            
            # Clear cache to force refresh
            self._last_cache_update = datetime.min
            
            logger.info(f"Created dynamic rule for {ip_address}: {action.value} for {duration_seconds}s")
            return rule
    
    async def log_security_event(
        self,
        ip_address: str,
        event_type: str,
        threat_level: ThreatLevel,
        description: str,
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> SecurityEvent:
        """Log a security event"""
        
        async with get_db_session() as session:
            event = SecurityEvent(
                event_type=event_type,
                threat_level=threat_level,
                title=f"IP Security Event: {event_type}",
                description=description,
                source_ip=ip_address,
                organization_id=organization_id,
                user_id=user_id,
                event_metadata=metadata or {}
            )
            
            session.add(event)
            await session.commit()
            await session.refresh(event)
            
            logger.info(f"Logged security event: {event_type} from {ip_address} - {threat_level.value}")
            return event


# Global instance
_ip_whitelist_manager: Optional[IPWhitelistManager] = None


def get_ip_whitelist_manager() -> IPWhitelistManager:
    """Get IP whitelist manager instance"""
    global _ip_whitelist_manager
    if _ip_whitelist_manager is None:
        _ip_whitelist_manager = IPWhitelistManager()
    return _ip_whitelist_manager


async def initialize_ip_whitelist_manager() -> IPWhitelistManager:
    """Initialize and start IP whitelist manager"""
    manager = get_ip_whitelist_manager()
    await manager.start_monitoring()
    return manager