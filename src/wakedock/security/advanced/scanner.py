"""
Security Scanner

Provides comprehensive security scanning capabilities including:
- Vulnerability assessment
- Threat detection
- Behavioral analysis
- Real-time monitoring
- Automated response
"""

import logging
import asyncio
import re
import hashlib
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, deque

from wakedock.database import get_db_session
from wakedock.security.advanced.models import SecurityEvent, ThreatLevel, SecurityRule, SecurityActionType
from wakedock.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """Security scan result"""
    scan_id: str
    target: str
    scan_type: str
    threat_level: ThreatLevel
    vulnerabilities: List[Dict]
    recommendations: List[str]
    score: float  # 0-100, higher is more secure
    timestamp: datetime


@dataclass
class ThreatIndicator:
    """Threat indicator"""
    indicator_type: str
    value: str
    confidence: float  # 0-1
    severity: ThreatLevel
    description: str
    source: str


@dataclass
class BehaviorPattern:
    """Behavioral pattern analysis"""
    pattern_id: str
    pattern_type: str
    description: str
    risk_score: float
    occurrences: int
    first_seen: datetime
    last_seen: datetime


class SecurityScanner:
    """Comprehensive security scanner and threat detector"""
    
    def __init__(self):
        self.settings = get_settings()
        self._scan_tasks: Dict[str, asyncio.Task] = {}
        self._threat_patterns: Dict[str, re.Pattern] = {}
        self._behavioral_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._monitoring_task = None
        
        # Initialize threat patterns
        self._load_threat_patterns()
        
        # Scanner configuration
        self.scan_interval = 300  # 5 minutes
        self.behavioral_window = 3600  # 1 hour
        self.max_concurrent_scans = 5
        
    def _load_threat_patterns(self):
        """Load threat detection patterns"""
        
        # SQL injection patterns
        self._threat_patterns.update({
            "sql_injection": re.compile(
                r"(union\s+select|insert\s+into|delete\s+from|drop\s+table|"
                r"or\s+1\s*=\s*1|and\s+1\s*=\s*1|'.*or.*'|\".*or.*\"|"
                r"exec\s*\(|sp_|xp_)", re.IGNORECASE
            ),
            "xss": re.compile(
                r"(<script|javascript:|onload=|onerror=|"
                r"<iframe|<object|<embed|eval\(|alert\()", re.IGNORECASE
            ),
            "path_traversal": re.compile(
                r"(\.\./|\.\.\\|\.\.\%2f|\.\.\%5c)", re.IGNORECASE
            ),
            "command_injection": re.compile(
                r"(;|\||&|\$\(|`|nc\s|netcat|wget|curl|chmod|rm\s|"
                r"cat\s|ls\s|ps\s|id\s|whoami|uname)", re.IGNORECASE
            ),
            "directory_listing": re.compile(
                r"(\.\.%2f|\.\.%5c|\.\.\/|\.\.\\)", re.IGNORECASE
            )
        })
        
        # Suspicious user agents
        self._threat_patterns["suspicious_ua"] = re.compile(
            r"(sqlmap|nmap|nikto|burp|acunetix|nessus|openvas|"
            r"w3af|skipfish|grabber|fimap|havij|pangolin)", re.IGNORECASE
        )
        
        # Suspicious file extensions
        self._threat_patterns["suspicious_files"] = re.compile(
            r"\.(php|asp|aspx|jsp|cgi|pl|py|rb|sh|cmd|bat|exe|dll)$", re.IGNORECASE
        )
    
    async def start_monitoring(self):
        """Start security monitoring"""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Security scanner monitoring started")
    
    async def stop_monitoring(self):
        """Stop security monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
        
        # Cancel all active scans
        for scan_id, task in self._scan_tasks.items():
            task.cancel()
        self._scan_tasks.clear()
        
        logger.info("Security scanner monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                await self._perform_periodic_scans()
                await self._analyze_behavioral_patterns()
                await self._cleanup_old_data()
                await asyncio.sleep(self.scan_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Security scanner monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _perform_periodic_scans(self):
        """Perform periodic security scans"""
        # This would implement various security scans
        # For now, we'll focus on behavioral analysis and threat detection
        pass
    
    async def _analyze_behavioral_patterns(self):
        """Analyze behavioral patterns for anomalies"""
        try:
            current_time = datetime.utcnow()
            cutoff_time = current_time - timedelta(seconds=self.behavioral_window)
            
            # Analyze patterns for each IP
            for ip_address, events in self._behavioral_data.items():
                if not events:
                    continue
                
                # Filter recent events
                recent_events = [e for e in events if e["timestamp"] > cutoff_time]
                if not recent_events:
                    continue
                
                # Analyze request patterns
                patterns = await self._detect_suspicious_patterns(ip_address, recent_events)
                
                for pattern in patterns:
                    await self._handle_suspicious_behavior(ip_address, pattern)
                    
        except Exception as e:
            logger.error(f"Behavioral analysis error: {e}")
    
    async def _detect_suspicious_patterns(self, ip_address: str, events: List[Dict]) -> List[BehaviorPattern]:
        """Detect suspicious behavioral patterns"""
        patterns = []
        
        # High request rate detection
        request_count = len(events)
        if request_count > 100:  # More than 100 requests in the window
            patterns.append(BehaviorPattern(
                pattern_id=f"high_rate_{ip_address}",
                pattern_type="high_request_rate",
                description=f"High request rate: {request_count} requests in {self.behavioral_window}s",
                risk_score=min(100.0, request_count / 10.0),
                occurrences=request_count,
                first_seen=events[0]["timestamp"],
                last_seen=events[-1]["timestamp"]
            ))
        
        # Error rate analysis
        error_events = [e for e in events if e.get("status_code", 200) >= 400]
        error_rate = len(error_events) / len(events) if events else 0
        
        if error_rate > 0.5:  # More than 50% errors
            patterns.append(BehaviorPattern(
                pattern_id=f"high_error_{ip_address}",
                pattern_type="high_error_rate",
                description=f"High error rate: {error_rate:.1%}",
                risk_score=error_rate * 100,
                occurrences=len(error_events),
                first_seen=error_events[0]["timestamp"] if error_events else datetime.utcnow(),
                last_seen=error_events[-1]["timestamp"] if error_events else datetime.utcnow()
            ))
        
        # Scanning behavior detection
        unique_paths = set(e.get("path", "") for e in events)
        if len(unique_paths) > 50:  # Accessing many different paths
            patterns.append(BehaviorPattern(
                pattern_id=f"scanning_{ip_address}",
                pattern_type="scanning_behavior",
                description=f"Scanning behavior: {len(unique_paths)} unique paths accessed",
                risk_score=min(100.0, len(unique_paths)),
                occurrences=len(unique_paths),
                first_seen=events[0]["timestamp"],
                last_seen=events[-1]["timestamp"]
            ))
        
        # Authentication attempts
        auth_events = [e for e in events if "login" in e.get("path", "").lower() or "auth" in e.get("path", "").lower()]
        failed_auth = [e for e in auth_events if e.get("status_code", 200) in [401, 403]]
        
        if len(failed_auth) > 10:  # More than 10 failed auth attempts
            patterns.append(BehaviorPattern(
                pattern_id=f"bruteforce_{ip_address}",
                pattern_type="brute_force",
                description=f"Possible brute force: {len(failed_auth)} failed authentication attempts",
                risk_score=min(100.0, len(failed_auth) * 5),
                occurrences=len(failed_auth),
                first_seen=failed_auth[0]["timestamp"] if failed_auth else datetime.utcnow(),
                last_seen=failed_auth[-1]["timestamp"] if failed_auth else datetime.utcnow()
            ))
        
        return patterns
    
    async def _handle_suspicious_behavior(self, ip_address: str, pattern: BehaviorPattern):
        """Handle detected suspicious behavior"""
        
        # Determine threat level
        threat_level = ThreatLevel.LOW
        if pattern.risk_score > 80:
            threat_level = ThreatLevel.CRITICAL
        elif pattern.risk_score > 60:
            threat_level = ThreatLevel.HIGH
        elif pattern.risk_score > 40:
            threat_level = ThreatLevel.MEDIUM
        
        # Log security event
        await self._log_security_event(
            event_type=pattern.pattern_type,
            threat_level=threat_level,
            ip_address=ip_address,
            description=pattern.description,
            event_metadata={
                "pattern_id": pattern.pattern_id,
                "risk_score": pattern.risk_score,
                "occurrences": pattern.occurrences
            }
        )
        
        # Take automated action based on severity
        if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            await self._take_automated_action(ip_address, pattern, threat_level)
    
    async def _take_automated_action(self, ip_address: str, pattern: BehaviorPattern, threat_level: ThreatLevel):
        """Take automated security action"""
        
        try:
            # Import here to avoid circular imports
            from wakedock.security.advanced.ip_whitelist import get_ip_whitelist_manager
            
            ip_manager = get_ip_whitelist_manager()
            
            # Determine action based on pattern and threat level
            if pattern.pattern_type in ["brute_force", "scanning_behavior"]:
                # Temporary block for scanning/brute force
                duration = 3600 if threat_level == ThreatLevel.HIGH else 7200  # 1-2 hours
                
                await ip_manager.create_dynamic_rule(
                    ip_address=ip_address,
                    action=SecurityActionType.BLOCK_TEMPORARY,
                    duration_seconds=duration,
                    reason=f"Automated block: {pattern.description}",
                    user_id=1,  # System user
                    organization_id=None
                )
                
                logger.warning(f"Temporarily blocked IP {ip_address} for {duration}s due to {pattern.pattern_type}")
            
            elif pattern.pattern_type == "high_request_rate":
                # Rate limiting (would integrate with rate limiter)
                logger.warning(f"Rate limiting recommended for IP {ip_address}")
            
        except Exception as e:
            logger.error(f"Failed to take automated action for {ip_address}: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old behavioral data"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)  # Keep 24 hours of data
        
        for ip_address in list(self._behavioral_data.keys()):
            events = self._behavioral_data[ip_address]
            
            # Remove old events
            while events and events[0]["timestamp"] < cutoff_time:
                events.popleft()
            
            # Remove empty entries
            if not events:
                del self._behavioral_data[ip_address]
    
    async def scan_request(self, request_data: Dict) -> List[ThreatIndicator]:
        """Scan a single request for threats"""
        threats = []
        
        ip_address = request_data.get("ip_address", "")
        user_agent = request_data.get("user_agent", "")
        path = request_data.get("path", "")
        query_string = request_data.get("query_string", "")
        headers = request_data.get("headers", {})
        body = request_data.get("body", "")
        
        # Combine all request data for pattern matching
        request_content = f"{path} {query_string} {body}".lower()
        
        # Check for SQL injection
        if self._threat_patterns["sql_injection"].search(request_content):
            threats.append(ThreatIndicator(
                indicator_type="sql_injection",
                value=path,
                confidence=0.8,
                severity=ThreatLevel.HIGH,
                description="Potential SQL injection attempt detected",
                source="pattern_match"
            ))
        
        # Check for XSS
        if self._threat_patterns["xss"].search(request_content):
            threats.append(ThreatIndicator(
                indicator_type="xss",
                value=path,
                confidence=0.7,
                severity=ThreatLevel.MEDIUM,
                description="Potential XSS attempt detected",
                source="pattern_match"
            ))
        
        # Check for path traversal
        if self._threat_patterns["path_traversal"].search(request_content):
            threats.append(ThreatIndicator(
                indicator_type="path_traversal",
                value=path,
                confidence=0.9,
                severity=ThreatLevel.HIGH,
                description="Path traversal attempt detected",
                source="pattern_match"
            ))
        
        # Check for command injection
        if self._threat_patterns["command_injection"].search(request_content):
            threats.append(ThreatIndicator(
                indicator_type="command_injection",
                value=path,
                confidence=0.8,
                severity=ThreatLevel.CRITICAL,
                description="Command injection attempt detected",
                source="pattern_match"
            ))
        
        # Check user agent
        if self._threat_patterns["suspicious_ua"].search(user_agent):
            threats.append(ThreatIndicator(
                indicator_type="suspicious_user_agent",
                value=user_agent,
                confidence=0.9,
                severity=ThreatLevel.MEDIUM,
                description="Suspicious user agent detected",
                source="pattern_match"
            ))
        
        # Check for suspicious file access
        if self._threat_patterns["suspicious_files"].search(path):
            threats.append(ThreatIndicator(
                indicator_type="suspicious_file_access",
                value=path,
                confidence=0.6,
                severity=ThreatLevel.MEDIUM,
                description="Access to potentially dangerous file type",
                source="pattern_match"
            ))
        
        # Record behavioral data
        self._record_request_behavior(request_data)
        
        return threats
    
    def _record_request_behavior(self, request_data: Dict):
        """Record request data for behavioral analysis"""
        ip_address = request_data.get("ip_address", "unknown")
        
        behavior_record = {
            "timestamp": datetime.utcnow(),
            "path": request_data.get("path", ""),
            "method": request_data.get("method", ""),
            "status_code": request_data.get("status_code", 200),
            "user_agent": request_data.get("user_agent", ""),
            "size": request_data.get("response_size", 0)
        }
        
        self._behavioral_data[ip_address].append(behavior_record)
    
    async def _log_security_event(
        self,
        event_type: str,
        threat_level: ThreatLevel,
        ip_address: str,
        description: str,
        metadata: Optional[Dict] = None
    ):
        """Log a security event"""
        
        async with get_db_session() as session:
            event = SecurityEvent(
                event_type=event_type,
                threat_level=threat_level,
                title=f"Security Scanner: {event_type}",
                description=description,
                source_ip=ip_address,
                event_metadata=metadata or {}
            )
            
            session.add(event)
            await session.commit()
            
            logger.info(f"Logged security event: {event_type} from {ip_address} - {threat_level.value}")
    
    async def perform_comprehensive_scan(self, target: str, scan_type: str = "full") -> ScanResult:
        """Perform a comprehensive security scan"""
        
        scan_id = hashlib.md5(f"{target}_{scan_type}_{datetime.utcnow()}".encode()).hexdigest()
        
        vulnerabilities = []
        recommendations = []
        score = 100.0  # Start with perfect score
        
        # This would implement various security checks
        # For demonstration, we'll include some basic checks
        
        if scan_type in ["full", "configuration"]:
            # Check for security misconfigurations
            config_vulns = await self._scan_configuration(target)
            vulnerabilities.extend(config_vulns)
            score -= len(config_vulns) * 10
        
        if scan_type in ["full", "network"]:
            # Check for network vulnerabilities
            network_vulns = await self._scan_network(target)
            vulnerabilities.extend(network_vulns)
            score -= len(network_vulns) * 15
        
        if scan_type in ["full", "application"]:
            # Check for application vulnerabilities
            app_vulns = await self._scan_application(target)
            vulnerabilities.extend(app_vulns)
            score -= len(app_vulns) * 20
        
        # Generate recommendations based on findings
        if vulnerabilities:
            recommendations.append("Address identified vulnerabilities immediately")
            recommendations.append("Implement regular security scanning")
            recommendations.append("Enable comprehensive logging and monitoring")
        
        # Determine threat level
        threat_level = ThreatLevel.LOW
        if score < 30:
            threat_level = ThreatLevel.CRITICAL
        elif score < 50:
            threat_level = ThreatLevel.HIGH
        elif score < 70:
            threat_level = ThreatLevel.MEDIUM
        
        return ScanResult(
            scan_id=scan_id,
            target=target,
            scan_type=scan_type,
            threat_level=threat_level,
            vulnerabilities=vulnerabilities,
            recommendations=recommendations,
            score=max(0.0, score),
            timestamp=datetime.utcnow()
        )
    
    async def _scan_configuration(self, target: str) -> List[Dict]:
        """Scan for configuration vulnerabilities"""
        vulns = []
        
        # Placeholder - would implement actual configuration checks
        # For example: check for default passwords, weak encryption, etc.
        
        return vulns
    
    async def _scan_network(self, target: str) -> List[Dict]:
        """Scan for network vulnerabilities"""
        vulns = []
        
        # Placeholder - would implement network security checks
        # For example: open ports, firewall rules, etc.
        
        return vulns
    
    async def _scan_application(self, target: str) -> List[Dict]:
        """Scan for application vulnerabilities"""
        vulns = []
        
        # Placeholder - would implement application security checks
        # For example: dependency vulnerabilities, code analysis, etc.
        
        return vulns
    
    async def get_threat_statistics(self, organization_id: Optional[int] = None) -> Dict[str, Any]:
        """Get threat detection statistics"""
        
        async with get_db_session() as session:
            # Get recent security events
            query = session.query(SecurityEvent)
            if organization_id:
                query = query.filter(SecurityEvent.organization_id == organization_id)
            
            # Last 24 hours
            since_date = datetime.utcnow() - timedelta(hours=24)
            events = await query.filter(SecurityEvent.timestamp >= since_date).all()
            
            # Analyze statistics
            total_events = len(events)
            threat_levels = defaultdict(int)
            event_types = defaultdict(int)
            blocked_events = 0
            
            for event in events:
                threat_levels[event.threat_level.value] += 1
                event_types[event.event_type] += 1
                if event.blocked:
                    blocked_events += 1
            
            return {
                "total_events": total_events,
                "blocked_events": blocked_events,
                "threat_levels": dict(threat_levels),
                "event_types": dict(event_types),
                "active_behavioral_profiles": len(self._behavioral_data),
                "scan_period": "24 hours"
            }


# Global instance
_security_scanner: Optional[SecurityScanner] = None


def get_security_scanner() -> SecurityScanner:
    """Get security scanner instance"""
    global _security_scanner
    if _security_scanner is None:
        _security_scanner = SecurityScanner()
    return _security_scanner


async def initialize_security_scanner() -> SecurityScanner:
    """Initialize and start security scanner"""
    scanner = get_security_scanner()
    await scanner.start_monitoring()
    return scanner