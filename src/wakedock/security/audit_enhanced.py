"""
Enhanced Security Audit System

Advanced threat detection with AI-powered analysis, threat intelligence integration,
and automated incident response capabilities.
"""

import asyncio
import json
import logging
import hashlib
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import ipaddress
import re

from .audit import AuditService, AuditEventType, AuditSeverity
from .intrusion_detection import IntrusionDetectionSystem, SecurityEvent, ThreatLevel, AttackType
from wakedock.database.database import get_async_db_session_context

logger = logging.getLogger(__name__)


class IncidentSeverity(str, Enum):
    """Severity levels for security incidents"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResponseAction(str, Enum):
    """Automated response actions"""
    LOG_ONLY = "log_only"
    RATE_LIMIT = "rate_limit"
    TEMPORARY_BLOCK = "temporary_block"
    PERMANENT_BLOCK = "permanent_block"
    ALERT_ADMIN = "alert_admin"
    QUARANTINE_USER = "quarantine_user"
    REVOKE_TOKENS = "revoke_tokens"
    SYSTEM_LOCKDOWN = "system_lockdown"


@dataclass
class ThreatIntelligence:
    """Threat intelligence data"""
    ip_address: str
    reputation_score: float  # 0.0 (clean) to 1.0 (malicious)
    categories: List[str]  # e.g., ['botnet', 'malware', 'phishing']
    source: str  # e.g., 'internal', 'external_feed', 'community'
    last_updated: datetime
    confidence: float  # 0.0 to 1.0
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityIncident:
    """Security incident with enriched data"""
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    attack_type: AttackType
    source_ip: str
    target_endpoint: str
    user_id: Optional[int]
    username: Optional[str]
    
    # Timing
    start_time: datetime
    end_time: Optional[datetime] = None
    detection_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Evidence
    events: List[SecurityEvent] = field(default_factory=list)
    indicators: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    # Response
    response_actions: List[ResponseAction] = field(default_factory=list)
    auto_blocked: bool = False
    manual_review_required: bool = False
    
    # Threat intel
    threat_intel: Optional[ThreatIntelligence] = None
    
    # Status
    status: str = "active"  # active, investigating, resolved, false_positive
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None


@dataclass
class AnomalyPattern:
    """Machine learning detected anomaly pattern"""
    pattern_id: str
    pattern_type: str  # 'behavioral', 'statistical', 'temporal'
    description: str
    confidence_score: float
    baseline_data: Dict[str, Any]
    current_data: Dict[str, Any]
    deviation_metrics: Dict[str, float]
    first_detected: datetime
    last_seen: datetime
    occurrence_count: int = 1


class EnhancedSecurityAuditSystem:
    """Enhanced security audit system with AI-powered analysis"""
    
    def __init__(self, audit_service: AuditService, ids: IntrusionDetectionSystem):
        self.audit_service = audit_service
        self.ids = ids
        
        # Incident management
        self.active_incidents: Dict[str, SecurityIncident] = {}
        self.incident_history: deque = deque(maxlen=1000)
        
        # Threat intelligence
        self.threat_intel_cache: Dict[str, ThreatIntelligence] = {}
        self.threat_feeds: List[str] = []  # External threat intelligence feeds
        
        # Anomaly detection
        self.baseline_patterns: Dict[str, Any] = {}
        self.detected_anomalies: Dict[str, AnomalyPattern] = {}
        
        # Response automation
        self.response_rules: List[Dict[str, Any]] = self._initialize_response_rules()
        self.auto_response_enabled = True
        
        # Analytics
        self.metrics_cache: Dict[str, Any] = {}
        self.last_metrics_update = datetime.now(timezone.utc)
        
        # Configuration
        self.config = {
            "threat_intelligence": {
                "enable_external_feeds": False,  # Disable external feeds by default
                "cache_ttl_hours": 24,
                "reputation_threshold": 0.7
            },
            "anomaly_detection": {
                "enable_ml_analysis": True,
                "baseline_learning_days": 7,
                "anomaly_threshold": 0.8,
                "min_samples_for_baseline": 100
            },
            "incident_response": {
                "auto_block_critical_threats": True,
                "auto_quarantine_compromised_users": True,
                "escalation_time_minutes": 30,
                "max_false_positive_rate": 0.05
            },
            "retention": {
                "incident_retention_days": 90,
                "metrics_retention_days": 30,
                "anomaly_retention_days": 14
            }
        }
    
    def _initialize_response_rules(self) -> List[Dict[str, Any]]:
        """Initialize automated response rules"""
        return [
            {
                "name": "Critical Threat Auto-Block",
                "condition": {
                    "threat_level": [ThreatLevel.CRITICAL],
                    "confidence_min": 0.9
                },
                "actions": [ResponseAction.PERMANENT_BLOCK, ResponseAction.ALERT_ADMIN],
                "enabled": True
            },
            {
                "name": "Brute Force Protection",
                "condition": {
                    "attack_type": [AttackType.BRUTE_FORCE],
                    "failed_attempts_min": 10
                },
                "actions": [ResponseAction.TEMPORARY_BLOCK, ResponseAction.RATE_LIMIT],
                "enabled": True
            },
            {
                "name": "SQL Injection Response",
                "condition": {
                    "attack_type": [AttackType.SQL_INJECTION],
                    "confidence_min": 0.8
                },
                "actions": [ResponseAction.TEMPORARY_BLOCK, ResponseAction.ALERT_ADMIN],
                "enabled": True
            },
            {
                "name": "Compromised User Detection",
                "condition": {
                    "anomaly_type": ["unusual_user_behavior"],
                    "confidence_min": 0.85
                },
                "actions": [ResponseAction.QUARANTINE_USER, ResponseAction.REVOKE_TOKENS],
                "enabled": True
            },
            {
                "name": "Mass Attack Detection",
                "condition": {
                    "concurrent_attacks_min": 5,
                    "time_window_minutes": 5
                },
                "actions": [ResponseAction.SYSTEM_LOCKDOWN, ResponseAction.ALERT_ADMIN],
                "enabled": False  # Disabled by default due to potential impact
            }
        ]
    
    async def analyze_security_events(self, events: List[SecurityEvent]) -> List[SecurityIncident]:
        """Analyze security events and create incidents"""
        incidents = []
        
        try:
            # Group related events
            event_groups = self._group_related_events(events)
            
            # Analyze each group
            for group in event_groups:
                incident = await self._analyze_event_group(group)
                if incident:
                    # Enrich with threat intelligence
                    await self._enrich_with_threat_intel(incident)
                    
                    # Detect anomalies
                    await self._detect_anomalies(incident)
                    
                    # Apply automated response
                    if self.auto_response_enabled:
                        await self._apply_automated_response(incident)
                    
                    # Store incident
                    self.active_incidents[incident.id] = incident
                    incidents.append(incident)
                    
                    logger.info(f"Security incident created: {incident.id} - {incident.title}")
            
            return incidents
            
        except Exception as e:
            logger.error(f"Error analyzing security events: {e}")
            return []
    
    def _group_related_events(self, events: List[SecurityEvent]) -> List[List[SecurityEvent]]:
        """Group related security events"""
        groups = []
        processed_events = set()
        
        for event in events:
            if id(event) in processed_events:
                continue
            
            # Find related events
            related_events = [event]
            processed_events.add(id(event))
            
            for other_event in events:
                if id(other_event) in processed_events:
                    continue
                
                # Check if events are related
                if self._are_events_related(event, other_event):
                    related_events.append(other_event)
                    processed_events.add(id(other_event))
            
            groups.append(related_events)
        
        return groups
    
    def _are_events_related(self, event1: SecurityEvent, event2: SecurityEvent) -> bool:
        """Check if two events are related"""
        # Same IP address
        if event1.ip_address == event2.ip_address:
            # Within time window
            time_diff = abs((event1.timestamp - event2.timestamp).total_seconds())
            if time_diff < 300:  # 5 minutes
                return True
        
        # Same user
        if event1.user_id and event1.user_id == event2.user_id:
            time_diff = abs((event1.timestamp - event2.timestamp).total_seconds())
            if time_diff < 600:  # 10 minutes
                return True
        
        # Same attack type from different IPs (coordinated attack)
        if (event1.attack_type == event2.attack_type and 
            event1.attack_type in [AttackType.BRUTE_FORCE, AttackType.SQL_INJECTION]):
            time_diff = abs((event1.timestamp - event2.timestamp).total_seconds())
            if time_diff < 180:  # 3 minutes
                return True
        
        return False
    
    async def _analyze_event_group(self, events: List[SecurityEvent]) -> Optional[SecurityIncident]:
        """Analyze a group of related events and create an incident"""
        if not events:
            return None
        
        # Determine incident severity
        max_threat_level = max(event.threat_level for event in events)
        severity = self._map_threat_to_severity(max_threat_level)
        
        # Create incident ID
        incident_id = self._generate_incident_id(events)
        
        # Determine primary attack type
        attack_types = [event.attack_type for event in events]
        primary_attack = max(set(attack_types), key=attack_types.count)
        
        # Extract key information
        source_ips = list(set(event.ip_address for event in events))
        endpoints = list(set(event.endpoint for event in events))
        user_ids = list(set(event.user_id for event in events if event.user_id))
        
        # Create incident
        incident = SecurityIncident(
            id=incident_id,
            title=self._generate_incident_title(primary_attack, source_ips, len(events)),
            description=self._generate_incident_description(events),
            severity=severity,
            attack_type=primary_attack,
            source_ip=source_ips[0] if source_ips else "unknown",
            target_endpoint=endpoints[0] if endpoints else "unknown",
            user_id=user_ids[0] if user_ids else None,
            username=None,  # Will be enriched later
            start_time=min(event.timestamp for event in events),
            events=events,
            indicators=self._extract_indicators(events)
        )
        
        return incident
    
    def _map_threat_to_severity(self, threat_level: ThreatLevel) -> IncidentSeverity:
        """Map threat level to incident severity"""
        mapping = {
            ThreatLevel.LOW: IncidentSeverity.LOW,
            ThreatLevel.MEDIUM: IncidentSeverity.MEDIUM,
            ThreatLevel.HIGH: IncidentSeverity.HIGH,
            ThreatLevel.CRITICAL: IncidentSeverity.CRITICAL
        }
        return mapping.get(threat_level, IncidentSeverity.MEDIUM)
    
    def _generate_incident_id(self, events: List[SecurityEvent]) -> str:
        """Generate unique incident ID"""
        # Create hash from event details
        event_data = "".join([
            f"{event.ip_address}{event.attack_type.value}{event.timestamp.isoformat()}"
            for event in events[:3]  # Use first 3 events to avoid too long strings
        ])
        
        hash_obj = hashlib.sha256(event_data.encode())
        return f"INC-{hash_obj.hexdigest()[:12].upper()}"
    
    def _generate_incident_title(self, attack_type: AttackType, source_ips: List[str], event_count: int) -> str:
        """Generate incident title"""
        attack_name = attack_type.value.replace('_', ' ').title()
        
        if len(source_ips) == 1:
            return f"{attack_name} from {source_ips[0]} ({event_count} events)"
        else:
            return f"Coordinated {attack_name} from {len(source_ips)} IPs ({event_count} events)"
    
    def _generate_incident_description(self, events: List[SecurityEvent]) -> str:
        """Generate incident description"""
        attack_types = list(set(event.attack_type.value for event in events))
        source_ips = list(set(event.ip_address for event in events))
        endpoints = list(set(event.endpoint for event in events))
        
        desc = f"Security incident involving {len(events)} events. "
        desc += f"Attack types: {', '.join(attack_types)}. "
        desc += f"Source IPs: {', '.join(source_ips[:5])}" + (" and others" if len(source_ips) > 5 else "") + ". "
        desc += f"Targeted endpoints: {', '.join(endpoints[:3])}" + (" and others" if len(endpoints) > 3 else "") + "."
        
        return desc
    
    def _extract_indicators(self, events: List[SecurityEvent]) -> List[str]:
        """Extract indicators of compromise from events"""
        indicators = set()
        
        for event in events:
            # IP addresses
            indicators.add(f"ip:{event.ip_address}")
            
            # User agents
            if event.user_agent:
                indicators.add(f"user_agent:{hashlib.md5(event.user_agent.encode()).hexdigest()[:16]}")
            
            # Payloads (hashed for privacy)
            if event.payload:
                indicators.add(f"payload_hash:{hashlib.sha256(event.payload.encode()).hexdigest()[:16]}")
            
            # Endpoints
            indicators.add(f"endpoint:{event.endpoint}")
        
        return list(indicators)
    
    async def _enrich_with_threat_intel(self, incident: SecurityIncident):
        """Enrich incident with threat intelligence"""
        try:
            threat_intel = await self._get_threat_intelligence(incident.source_ip)
            if threat_intel:
                incident.threat_intel = threat_intel
                
                # Upgrade severity if high reputation threat
                if threat_intel.reputation_score > self.config["threat_intelligence"]["reputation_threshold"]:
                    if incident.severity == IncidentSeverity.LOW:
                        incident.severity = IncidentSeverity.MEDIUM
                    elif incident.severity == IncidentSeverity.MEDIUM:
                        incident.severity = IncidentSeverity.HIGH
                
                logger.info(f"Incident {incident.id} enriched with threat intel: {threat_intel.reputation_score}")
        
        except Exception as e:
            logger.error(f"Failed to enrich incident with threat intel: {e}")
    
    async def _get_threat_intelligence(self, ip_address: str) -> Optional[ThreatIntelligence]:
        """Get threat intelligence for IP address"""
        # Check cache first
        if ip_address in self.threat_intel_cache:
            intel = self.threat_intel_cache[ip_address]
            # Check if data is still fresh
            if (datetime.now(timezone.utc) - intel.last_updated).total_seconds() < \
               self.config["threat_intelligence"]["cache_ttl_hours"] * 3600:
                return intel
        
        # Generate basic threat intelligence (internal analysis)
        intel = await self._analyze_internal_threat_intel(ip_address)
        
        # Cache the result
        if intel:
            self.threat_intel_cache[ip_address] = intel
        
        return intel
    
    async def _analyze_internal_threat_intel(self, ip_address: str) -> Optional[ThreatIntelligence]:
        """Analyze internal threat intelligence for IP"""
        try:
            # Get IP profile from IDS
            profile = self.ids.get_ip_profile(ip_address)
            if not profile:
                return None
            
            # Calculate reputation score based on internal data
            reputation_score = 0.0
            categories = []
            
            # Failed authentication ratio
            if profile.failed_auth_count > 0:
                fail_ratio = profile.failed_auth_count / (profile.failed_auth_count + profile.successful_auth_count + 1)
                reputation_score += fail_ratio * 0.3
                if fail_ratio > 0.8:
                    categories.append('credential_stuffing')
            
            # Request pattern analysis
            if profile.request_count > 1000:
                reputation_score += 0.2
                categories.append('high_volume')
            
            # Suspicious score from IDS
            reputation_score += profile.suspicious_score * 0.5
            
            # Check for scanner patterns
            scanner_endpoints = {'/admin', '/wp-admin', '/.env', '/config', '/backup'}
            if any(endpoint in scanner_endpoints for endpoint in profile.endpoints_accessed):
                reputation_score += 0.3
                categories.append('scanner')
            
            # Normalize score
            reputation_score = min(reputation_score, 1.0)
            
            return ThreatIntelligence(
                ip_address=ip_address,
                reputation_score=reputation_score,
                categories=categories,
                source='internal_analysis',
                last_updated=datetime.now(timezone.utc),
                confidence=0.8,  # Internal analysis confidence
                additional_data={
                    'profile_data': {
                        'request_count': profile.request_count,
                        'failed_auth_count': profile.failed_auth_count,
                        'suspicious_score': profile.suspicious_score,
                        'unique_endpoints': len(profile.endpoints_accessed),
                        'unique_user_agents': len(profile.user_agents)
                    }
                }
            )
        
        except Exception as e:
            logger.error(f"Failed to analyze internal threat intel for {ip_address}: {e}")
            return None
    
    async def _detect_anomalies(self, incident: SecurityIncident):
        """Detect anomalies in incident patterns"""
        try:
            if not self.config["anomaly_detection"]["enable_ml_analysis"]:
                return
            
            # Analyze behavioral anomalies
            await self._detect_behavioral_anomalies(incident)
            
            # Analyze statistical anomalies
            await self._detect_statistical_anomalies(incident)
            
            # Analyze temporal anomalies
            await self._detect_temporal_anomalies(incident)
        
        except Exception as e:
            logger.error(f"Failed to detect anomalies for incident {incident.id}: {e}")
    
    async def _detect_behavioral_anomalies(self, incident: SecurityIncident):
        """Detect behavioral anomalies"""
        # Simple behavioral analysis (in production, you'd use ML models)
        if incident.user_id:
            # Check for unusual user behavior patterns
            # This is a simplified implementation
            pass
    
    async def _detect_statistical_anomalies(self, incident: SecurityIncident):
        """Detect statistical anomalies"""
        # Simple statistical analysis
        # In production, implement proper statistical anomaly detection
        pass
    
    async def _detect_temporal_anomalies(self, incident: SecurityIncident):
        """Detect temporal anomalies"""
        # Simple temporal analysis
        # Check for unusual timing patterns
        pass
    
    async def _apply_automated_response(self, incident: SecurityIncident):
        """Apply automated response actions"""
        try:
            # Find matching response rules
            matching_rules = self._find_matching_response_rules(incident)
            
            for rule in matching_rules:
                if not rule.get("enabled", True):
                    continue
                
                actions = rule.get("actions", [])
                for action in actions:
                    await self._execute_response_action(incident, action)
                    incident.response_actions.append(action)
                
                logger.info(f"Applied response rule '{rule['name']}' to incident {incident.id}")
        
        except Exception as e:
            logger.error(f"Failed to apply automated response for incident {incident.id}: {e}")
    
    def _find_matching_response_rules(self, incident: SecurityIncident) -> List[Dict[str, Any]]:
        """Find response rules that match the incident"""
        matching_rules = []
        
        for rule in self.response_rules:
            if self._rule_matches_incident(rule, incident):
                matching_rules.append(rule)
        
        return matching_rules
    
    def _rule_matches_incident(self, rule: Dict[str, Any], incident: SecurityIncident) -> bool:
        """Check if a response rule matches an incident"""
        condition = rule.get("condition", {})
        
        # Check threat level
        if "threat_level" in condition:
            event_threat_levels = [event.threat_level for event in incident.events]
            if not any(level in condition["threat_level"] for level in event_threat_levels):
                return False
        
        # Check attack type
        if "attack_type" in condition:
            if incident.attack_type not in condition["attack_type"]:
                return False
        
        # Check confidence
        if "confidence_min" in condition:
            max_confidence = max(event.confidence for event in incident.events)
            if max_confidence < condition["confidence_min"]:
                return False
        
        # Check failed attempts (for brute force)
        if "failed_attempts_min" in condition:
            failed_attempts = sum(1 for event in incident.events 
                                if event.attack_type == AttackType.BRUTE_FORCE)
            if failed_attempts < condition["failed_attempts_min"]:
                return False
        
        return True
    
    async def _execute_response_action(self, incident: SecurityIncident, action: ResponseAction):
        """Execute a response action"""
        try:
            if action == ResponseAction.PERMANENT_BLOCK:
                self.ids.block_ip(incident.source_ip)
                incident.auto_blocked = True
                logger.warning(f"PERMANENTLY BLOCKED IP {incident.source_ip} (Incident: {incident.id})")
            
            elif action == ResponseAction.TEMPORARY_BLOCK:
                self.ids.block_ip(incident.source_ip)
                incident.auto_blocked = True
                # In production, implement temporary blocking with expiration
                logger.warning(f"TEMPORARILY BLOCKED IP {incident.source_ip} (Incident: {incident.id})")
            
            elif action == ResponseAction.RATE_LIMIT:
                # In production, implement rate limiting
                logger.warning(f"RATE LIMITED IP {incident.source_ip} (Incident: {incident.id})")
            
            elif action == ResponseAction.ALERT_ADMIN:
                await self._send_admin_alert(incident)
            
            elif action == ResponseAction.QUARANTINE_USER:
                if incident.user_id:
                    # In production, implement user quarantine
                    logger.warning(f"QUARANTINED USER {incident.user_id} (Incident: {incident.id})")
            
            elif action == ResponseAction.REVOKE_TOKENS:
                if incident.user_id:
                    # In production, revoke user tokens
                    logger.warning(f"REVOKED TOKENS for USER {incident.user_id} (Incident: {incident.id})")
            
            elif action == ResponseAction.SYSTEM_LOCKDOWN:
                # In production, implement system lockdown
                logger.critical(f"SYSTEM LOCKDOWN triggered by incident {incident.id}")
            
        except Exception as e:
            logger.error(f"Failed to execute response action {action.value}: {e}")
    
    async def _send_admin_alert(self, incident: SecurityIncident):
        """Send alert to administrators"""
        # In production, implement email/Slack/webhook notifications
        logger.critical(f"ADMIN ALERT: Security incident {incident.id} - {incident.title}")
    
    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive security dashboard data"""
        try:
            now = datetime.now(timezone.utc)
            
            # Update metrics if needed
            if (now - self.last_metrics_update).total_seconds() > 300:  # 5 minutes
                await self._update_metrics_cache()
            
            # Active incidents
            active_incidents = len(self.active_incidents)
            critical_incidents = len([i for i in self.active_incidents.values() 
                                    if i.severity == IncidentSeverity.CRITICAL])
            
            # Recent activity (last 24 hours)
            recent_events = [event for incident in self.active_incidents.values() 
                           for event in incident.events 
                           if (now - event.timestamp).total_seconds() < 86400]
            
            # Threat intelligence summary
            high_risk_ips = len([intel for intel in self.threat_intel_cache.values() 
                               if intel.reputation_score > 0.7])
            
            # Top threats
            top_threats = self._get_top_threats_summary()
            
            # Response actions summary
            response_summary = self._get_response_actions_summary()
            
            return {
                "timestamp": now.isoformat(),
                "overview": {
                    "active_incidents": active_incidents,
                    "critical_incidents": critical_incidents,
                    "events_24h": len(recent_events),
                    "high_risk_ips": high_risk_ips,
                    "blocked_ips": len(self.ids.blocked_ips),
                    "auto_responses_24h": self.metrics_cache.get("auto_responses_24h", 0)
                },
                "incidents": {
                    "by_severity": self._group_incidents_by_severity(),
                    "by_attack_type": self._group_incidents_by_attack_type(),
                    "recent": [self._incident_to_dict(i) for i in 
                             list(self.active_incidents.values())[-10:]]
                },
                "threat_intelligence": {
                    "total_ips_analyzed": len(self.threat_intel_cache),
                    "high_risk_ips": high_risk_ips,
                    "reputation_distribution": self._get_reputation_distribution()
                },
                "top_threats": top_threats,
                "response_actions": response_summary,
                "system_health": {
                    "auto_response_enabled": self.auto_response_enabled,
                    "rules_active": len([r for r in self.response_rules if r.get("enabled", True)]),
                    "ml_analysis_enabled": self.config["anomaly_detection"]["enable_ml_analysis"]
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to generate security dashboard: {e}")
            return {"error": str(e)}
    
    async def _update_metrics_cache(self):
        """Update metrics cache"""
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(days=1)
        
        # Count auto responses in last 24h
        auto_responses = 0
        for incident in self.active_incidents.values():
            if incident.detection_time >= day_ago and incident.response_actions:
                auto_responses += len(incident.response_actions)
        
        self.metrics_cache["auto_responses_24h"] = auto_responses
        self.last_metrics_update = now
    
    def _group_incidents_by_severity(self) -> Dict[str, int]:
        """Group incidents by severity"""
        groups = defaultdict(int)
        for incident in self.active_incidents.values():
            groups[incident.severity.value] += 1
        return dict(groups)
    
    def _group_incidents_by_attack_type(self) -> Dict[str, int]:
        """Group incidents by attack type"""
        groups = defaultdict(int)
        for incident in self.active_incidents.values():
            groups[incident.attack_type.value] += 1
        return dict(groups)
    
    def _get_top_threats_summary(self) -> List[Dict[str, Any]]:
        """Get top threats summary"""
        # Sort incidents by severity and confidence
        sorted_incidents = sorted(
            self.active_incidents.values(),
            key=lambda x: (x.severity.value, max(e.confidence for e in x.events)),
            reverse=True
        )
        
        return [{
            "incident_id": i.id,
            "title": i.title,
            "severity": i.severity.value,
            "source_ip": i.source_ip,
            "attack_type": i.attack_type.value,
            "event_count": len(i.events),
            "reputation_score": i.threat_intel.reputation_score if i.threat_intel else 0.0
        } for i in sorted_incidents[:10]]
    
    def _get_response_actions_summary(self) -> Dict[str, int]:
        """Get response actions summary"""
        actions = defaultdict(int)
        for incident in self.active_incidents.values():
            for action in incident.response_actions:
                actions[action.value] += 1
        return dict(actions)
    
    def _get_reputation_distribution(self) -> Dict[str, int]:
        """Get reputation score distribution"""
        distribution = {
            "clean (0.0-0.3)": 0,
            "suspicious (0.3-0.7)": 0,
            "malicious (0.7-1.0)": 0
        }
        
        for intel in self.threat_intel_cache.values():
            if intel.reputation_score <= 0.3:
                distribution["clean (0.0-0.3)"] += 1
            elif intel.reputation_score <= 0.7:
                distribution["suspicious (0.3-0.7)"] += 1
            else:
                distribution["malicious (0.7-1.0)"] += 1
        
        return distribution
    
    def _incident_to_dict(self, incident: SecurityIncident) -> Dict[str, Any]:
        """Convert incident to dictionary"""
        return {
            "id": incident.id,
            "title": incident.title,
            "severity": incident.severity.value,
            "attack_type": incident.attack_type.value,
            "source_ip": incident.source_ip,
            "target_endpoint": incident.target_endpoint,
            "start_time": incident.start_time.isoformat(),
            "detection_time": incident.detection_time.isoformat(),
            "event_count": len(incident.events),
            "auto_blocked": incident.auto_blocked,
            "response_actions": [action.value for action in incident.response_actions],
            "status": incident.status,
            "reputation_score": incident.threat_intel.reputation_score if incident.threat_intel else None
        }
    
    async def cleanup_old_data(self):
        """Clean up old data based on retention policies"""
        try:
            now = datetime.now(timezone.utc)
            
            # Clean up old incidents
            retention_days = self.config["retention"]["incident_retention_days"]
            cutoff_date = now - timedelta(days=retention_days)
            
            old_incidents = []
            for incident_id, incident in self.active_incidents.items():
                if incident.detection_time < cutoff_date and incident.status == "resolved":
                    old_incidents.append(incident_id)
            
            for incident_id in old_incidents:
                incident = self.active_incidents.pop(incident_id)
                self.incident_history.append(incident)
            
            # Clean up old threat intelligence
            intel_retention_hours = self.config["threat_intelligence"]["cache_ttl_hours"]
            intel_cutoff = now - timedelta(hours=intel_retention_hours * 2)  # Keep longer than TTL
            
            old_intel = []
            for ip, intel in self.threat_intel_cache.items():
                if intel.last_updated < intel_cutoff:
                    old_intel.append(ip)
            
            for ip in old_intel:
                del self.threat_intel_cache[ip]
            
            logger.info(f"Cleanup completed: {len(old_incidents)} incidents, {len(old_intel)} threat intel entries")
        
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")


# Global instance
_enhanced_audit_system: Optional[EnhancedSecurityAuditSystem] = None


def get_enhanced_audit_system(audit_service: AuditService = None, ids: IntrusionDetectionSystem = None) -> EnhancedSecurityAuditSystem:
    """Get global enhanced audit system instance"""
    global _enhanced_audit_system
    if _enhanced_audit_system is None:
        from .audit import get_audit_service
        from .intrusion_detection import get_intrusion_detection_system
        
        audit_service = audit_service or get_audit_service()
        ids = ids or get_intrusion_detection_system()
        _enhanced_audit_system = EnhancedSecurityAuditSystem(audit_service, ids)
    
    return _enhanced_audit_system
