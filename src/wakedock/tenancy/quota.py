"""
Quota Manager

Manages resource quotas and usage tracking for organizations including:
- Real-time quota enforcement
- Usage monitoring and alerts
- Automatic quota adjustments
- Resource cleanup
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from wakedock.database import get_db_session
from wakedock.database.models import Service
from wakedock.database.models.organization import Organization, UsageRecord, SubscriptionTier
# Lazy import to avoid circular dependency

logger = logging.getLogger(__name__)


@dataclass
class QuotaStatus:
    """Quota status information"""
    resource: str
    current: float
    limit: float
    percentage: float
    is_exceeded: bool
    is_warning: bool  # Above 80%


@dataclass
class QuotaAlert:
    """Quota alert information"""
    organization_id: int
    resource: str
    current: float
    limit: float
    percentage: float
    severity: str  # warning, critical
    message: str
    timestamp: datetime


class QuotaManager:
    """Manages resource quotas for organizations"""
    
    def __init__(self):
        self.tenancy_service = None  # Will be set during initialization
        self.orchestrator = None  # Will be set via dependency injection
        self.warning_threshold = 80.0  # Percentage
        self.critical_threshold = 95.0  # Percentage
        self._monitoring_task = None
        self._alerts: List[QuotaAlert] = []
    
    async def start_monitoring(self):
        """Start quota monitoring background task"""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Started quota monitoring")
    
    async def stop_monitoring(self):
        """Stop quota monitoring background task"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
            logger.info("Stopped quota monitoring")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await self.update_all_organization_usage()
                await self.check_quota_alerts()
                await asyncio.sleep(300)  # Check every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Quota monitoring error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def get_organization_quota_status(self, org_id: int) -> Dict[str, QuotaStatus]:
        """Get comprehensive quota status for organization"""
        async with get_db_session() as session:
            organization = await session.query(Organization).filter(
                Organization.id == org_id
            ).first()
            
            if not organization:
                raise ValueError(f"Organization {org_id} not found")
            
            quota_status = {}
            
            # Define resources to check
            resources = [
                ("containers", organization.current_containers, organization.max_containers),
                ("cpu_cores", float(organization.current_cpu_usage), float(organization.max_cpu_cores)),
                ("memory_gb", float(organization.current_memory_usage), float(organization.max_memory_gb)),
                ("storage_gb", float(organization.current_storage_usage), float(organization.max_storage_gb)),
                ("users", organization.current_users, organization.max_users),
                ("backups", organization.current_backups, organization.max_backups)
            ]
            
            for resource, current, limit in resources:
                # Handle unlimited quotas (enterprise tier)
                if limit == -1:
                    percentage = 0.0
                    is_exceeded = False
                else:
                    percentage = (current / limit * 100) if limit > 0 else 0
                    is_exceeded = current > limit
                
                is_warning = percentage >= self.warning_threshold and not is_exceeded
                
                quota_status[resource] = QuotaStatus(
                    resource=resource,
                    current=current,
                    limit=limit,
                    percentage=percentage,
                    is_exceeded=is_exceeded,
                    is_warning=is_warning
                )
            
            return quota_status
    
    async def update_organization_usage(self, org_id: int) -> Organization:
        """Update real-time usage statistics for organization"""
        async with get_db_session() as session:
            organization = await session.query(Organization).filter(
                Organization.id == org_id
            ).first()
            
            if not organization:
                raise ValueError(f"Organization {org_id} not found")
            
            # Get services for this organization
            services = await session.query(Service).filter(
                Service.organization_id == org_id
            ).all()
            
            # Update container count
            organization.current_containers = len(services)
            
            # Calculate resource usage from running containers
            total_cpu = 0.0
            total_memory = 0.0
            total_storage = 0.0
            
            if self.orchestrator:
                for service in services:
                    if service.container_id:
                        try:
                            # Get container stats
                            stats = await self.orchestrator.get_container_stats(service.container_id)
                            if stats:
                                # Extract CPU usage (convert from percentage to cores)
                                cpu_percent = stats.get("cpu_percent", 0)
                                total_cpu += cpu_percent / 100.0
                                
                                # Extract memory usage (convert to GB)
                                memory_usage = stats.get("memory", {}).get("usage", 0)
                                total_memory += memory_usage / (1024 ** 3)  # Bytes to GB
                                
                                # Estimate storage usage (simplified)
                                # In real implementation, this would check volume usage
                                total_storage += 1.0  # 1GB per container estimate
                        except Exception as e:
                            logger.warning(f"Failed to get stats for container {service.container_id}: {e}")
            
            # Update usage
            organization.current_cpu_usage = total_cpu
            organization.current_memory_usage = total_memory
            organization.current_storage_usage = total_storage
            
            # TODO: Update backup count from backup service
            # organization.current_backups = await self._get_backup_count(org_id)
            
            await session.commit()
            
            logger.debug(f"Updated usage for organization {org_id}: "
                        f"containers={organization.current_containers}, "
                        f"cpu={total_cpu:.2f}, memory={total_memory:.2f}GB")
            
            return organization
    
    async def update_all_organization_usage(self):
        """Update usage for all active organizations"""
        async with get_db_session() as session:
            organizations = await session.query(Organization).filter(
                Organization.is_active == True
            ).all()
            
            for organization in organizations:
                try:
                    await self.update_organization_usage(organization.id)
                except Exception as e:
                    logger.error(f"Failed to update usage for organization {organization.id}: {e}")
    
    async def check_quota_alerts(self):
        """Check for quota violations and generate alerts"""
        async with get_db_session() as session:
            organizations = await session.query(Organization).filter(
                Organization.is_active == True
            ).all()
            
            new_alerts = []
            
            for organization in organizations:
                try:
                    quota_status = await self.get_organization_quota_status(organization.id)
                    
                    for resource, status in quota_status.items():
                        # Skip unlimited resources
                        if status.limit == -1:
                            continue
                        
                        # Check for critical alerts (exceeded quota)
                        if status.is_exceeded:
                            alert = QuotaAlert(
                                organization_id=organization.id,
                                resource=resource,
                                current=status.current,
                                limit=status.limit,
                                percentage=status.percentage,
                                severity="critical",
                                message=f"Quota exceeded for {resource}: {status.current:.1f}/{status.limit:.1f}",
                                timestamp=datetime.utcnow()
                            )
                            new_alerts.append(alert)
                        
                        # Check for warning alerts (approaching quota)
                        elif status.percentage >= self.critical_threshold:
                            alert = QuotaAlert(
                                organization_id=organization.id,
                                resource=resource,
                                current=status.current,
                                limit=status.limit,
                                percentage=status.percentage,
                                severity="critical",
                                message=f"Quota critical for {resource}: {status.percentage:.1f}% used",
                                timestamp=datetime.utcnow()
                            )
                            new_alerts.append(alert)
                        
                        elif status.is_warning:
                            alert = QuotaAlert(
                                organization_id=organization.id,
                                resource=resource,
                                current=status.current,
                                limit=status.limit,
                                percentage=status.percentage,
                                severity="warning",
                                message=f"Quota warning for {resource}: {status.percentage:.1f}% used",
                                timestamp=datetime.utcnow()
                            )
                            new_alerts.append(alert)
                
                except Exception as e:
                    logger.error(f"Failed to check quotas for organization {organization.id}: {e}")
            
            # Store new alerts (in production, would send notifications)
            self._alerts.extend(new_alerts)
            
            # Keep only recent alerts (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self._alerts = [alert for alert in self._alerts if alert.timestamp > cutoff_time]
            
            if new_alerts:
                logger.info(f"Generated {len(new_alerts)} quota alerts")
    
    async def enforce_quota_limit(self, org_id: int, resource: str, requested_amount: float = 1) -> Tuple[bool, str]:
        """Enforce quota limit before resource allocation"""
        if not self.tenancy_service:
            return True, ""  # Allow if no tenancy service
        
        try:
            exceeded, message = await self.tenancy_service.check_quota_exceeded(
                org_id, resource, requested_amount
            )
            
            if exceeded:
                logger.warning(f"Quota enforcement blocked request: {message}")
                return False, message
            
            return True, ""
        
        except Exception as e:
            logger.error(f"Quota enforcement error: {e}")
            return True, ""  # Allow on error (fail open)
    
    async def allocate_resource(self, org_id: int, resource: str, amount: float = 1) -> bool:
        """Allocate resource and update usage"""
        # Check quota first
        allowed, message = await self.enforce_quota_limit(org_id, resource, amount)
        if not allowed:
            return False
        
        # Update current usage
        current_field = f"current_{resource}"
        try:
            async with get_db_session() as session:
                organization = await session.query(Organization).filter(
                    Organization.id == org_id
                ).first()
                
                if organization and hasattr(organization, current_field):
                    current_value = getattr(organization, current_field)
                    setattr(organization, current_field, current_value + amount)
                    await session.commit()
                    
                    logger.debug(f"Allocated {amount} {resource} to organization {org_id}")
                    return True
        
        except Exception as e:
            logger.error(f"Failed to allocate resource: {e}")
        
        return False
    
    async def deallocate_resource(self, org_id: int, resource: str, amount: float = 1) -> bool:
        """Deallocate resource and update usage"""
        current_field = f"current_{resource}"
        try:
            async with get_db_session() as session:
                organization = await session.query(Organization).filter(
                    Organization.id == org_id
                ).first()
                
                if organization and hasattr(organization, current_field):
                    current_value = getattr(organization, current_field)
                    new_value = max(0, current_value - amount)
                    setattr(organization, current_field, new_value)
                    await session.commit()
                    
                    logger.debug(f"Deallocated {amount} {resource} from organization {org_id}")
                    return True
        
        except Exception as e:
            logger.error(f"Failed to deallocate resource: {e}")
        
        return False
    
    async def get_recent_alerts(self, org_id: Optional[int] = None, limit: int = 50) -> List[QuotaAlert]:
        """Get recent quota alerts"""
        alerts = self._alerts
        
        if org_id:
            alerts = [alert for alert in alerts if alert.organization_id == org_id]
        
        # Sort by timestamp (newest first) and limit
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        return alerts[:limit]
    
    async def get_usage_trends(self, org_id: int, days: int = 30) -> Dict[str, List[Dict]]:
        """Get usage trends over time"""
        async with get_db_session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            usage_records = await session.query(UsageRecord).filter(
                UsageRecord.organization_id == org_id,
                UsageRecord.recorded_at >= start_date
            ).order_by(UsageRecord.recorded_at).all()
            
            trends = {
                "containers": [],
                "cpu": [],
                "memory": [],
                "storage": []
            }
            
            for record in usage_records:
                timestamp = record.recorded_at.isoformat()
                
                trends["containers"].append({
                    "timestamp": timestamp,
                    "value": record.containers_count
                })
                trends["cpu"].append({
                    "timestamp": timestamp,
                    "value": float(record.cpu_usage)
                })
                trends["memory"].append({
                    "timestamp": timestamp,
                    "value": float(record.memory_usage_gb)
                })
                trends["storage"].append({
                    "timestamp": timestamp,
                    "value": float(record.storage_usage_gb)
                })
            
            return trends
    
    async def cleanup_over_quota_resources(self, org_id: int):
        """Cleanup resources when over quota (emergency measure)"""
        quota_status = await self.get_organization_quota_status(org_id)
        
        # Stop oldest containers if over container quota
        if quota_status["containers"].is_exceeded:
            excess = int(quota_status["containers"].current - quota_status["containers"].limit)
            await self._stop_oldest_containers(org_id, excess)
        
        logger.warning(f"Emergency quota cleanup performed for organization {org_id}")
    
    async def _stop_oldest_containers(self, org_id: int, count: int):
        """Stop oldest containers to free up quota"""
        async with get_db_session() as session:
            services = await session.query(Service).filter(
                Service.organization_id == org_id,
                Service.container_id.isnot(None)
            ).order_by(Service.created_at).limit(count).all()
            
            for service in services:
                try:
                    if self.orchestrator:
                        await self.orchestrator.stop_service(service.name)
                        logger.info(f"Stopped service {service.name} for quota enforcement")
                except Exception as e:
                    logger.error(f"Failed to stop service {service.name}: {e}")


# Global instance
_quota_manager = None

def get_quota_manager() -> Optional[QuotaManager]:
    """Get the global quota manager instance"""
    return _quota_manager

def initialize_quota_manager() -> QuotaManager:
    """Initialize the global quota manager instance"""
    global _quota_manager
    _quota_manager = QuotaManager()
    
    # Set tenancy service reference after initialization to avoid circular imports
    from .service import get_tenancy_service
    _quota_manager.tenancy_service = get_tenancy_service()
    
    return _quota_manager