"""
Système de Détection d'Intrusion (IDS) pour WakeDock
Détecte les activités suspectes et les tentatives d'intrusion
"""

import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import ipaddress
from user_agents import parse as parse_user_agent
import hashlib

logger = logging.getLogger(__name__)

class ThreatLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AttackType(str, Enum):
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    DIRECTORY_TRAVERSAL = "directory_traversal"
    COMMAND_INJECTION = "command_injection"
    SUSPICIOUS_USER_AGENT = "suspicious_user_agent"
    RATE_LIMIT_ABUSE = "rate_limit_abuse"
    UNUSUAL_ACTIVITY = "unusual_activity"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"

@dataclass
class SecurityEvent:
    """Événement de sécurité détecté"""
    timestamp: datetime
    ip_address: str
    user_id: Optional[int]
    attack_type: AttackType
    threat_level: ThreatLevel
    details: Dict[str, Any]
    confidence: float  # 0.0 à 1.0
    endpoint: str
    user_agent: str
    payload: Optional[str] = None
    blocked: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "user_id": self.user_id,
            "attack_type": self.attack_type.value,
            "threat_level": self.threat_level.value,
            "details": self.details,
            "confidence": self.confidence,
            "endpoint": self.endpoint,
            "user_agent": self.user_agent,
            "payload": self.payload,
            "blocked": self.blocked
        }

@dataclass
class IPProfile:
    """Profile comportemental d'une adresse IP"""
    ip_address: str
    first_seen: datetime
    last_seen: datetime
    request_count: int = 0
    failed_auth_count: int = 0
    successful_auth_count: int = 0
    endpoints_accessed: Set[str] = field(default_factory=set)
    user_agents: Set[str] = field(default_factory=set)
    countries: Set[str] = field(default_factory=set)
    suspicious_score: float = 0.0
    is_blacklisted: bool = False
    is_whitelisted: bool = False
    
    def update_activity(self, endpoint: str, user_agent: str, success: bool = True):
        """Met à jour l'activité de l'IP"""
        self.last_seen = datetime.now(timezone.utc)
        self.request_count += 1
        self.endpoints_accessed.add(endpoint)
        self.user_agents.add(user_agent)
        
        if endpoint.startswith("/auth/"):
            if success:
                self.successful_auth_count += 1
            else:
                self.failed_auth_count += 1

class IntrusionDetectionSystem:
    """Système de détection d'intrusion"""
    
    def __init__(self):
        # Patterns de détection
        self.sql_injection_patterns = [
            r"union\s+select",
            r"drop\s+table",
            r"exec\s*\(",
            r"script\s*>",
            r"<\s*script",
            r"eval\s*\(",
            r"or\s+1\s*=\s*1",
            r"'\s*or\s*'1'\s*=\s*'1",
            r"admin'\s*--",
            r"'\s*;\s*drop\s+table",
            r"union\s+all\s+select",
            r"information_schema",
            r"concat\s*\(",
            r"char\s*\(",
            r"ascii\s*\(",
            r"benchmark\s*\(",
            r"sleep\s*\(",
            r"waitfor\s+delay"
        ]
        
        self.xss_patterns = [
            r"<script",
            r"javascript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"onmouseover\s*=",
            r"eval\s*\(",
            r"alert\s*\(",
            r"confirm\s*\(",
            r"prompt\s*\(",
            r"document\.cookie",
            r"document\.write",
            r"window\.location",
            r"<iframe",
            r"<embed",
            r"<object"
        ]
        
        self.directory_traversal_patterns = [
            r"\.\.\/",
            r"\.\.\\",
            r"\.\.%2f",
            r"\.\.%5c",
            r"..%252f",
            r"..%255c",
            r"etc\/passwd",
            r"etc\\passwd",
            r"boot\.ini",
            r"win\.ini"
        ]
        
        self.command_injection_patterns = [
            r";\s*ls",
            r";\s*cat",
            r";\s*wget",
            r";\s*curl",
            r";\s*nc",
            r";\s*rm",
            r";\s*chmod",
            r";\s*sudo",
            r"\|\s*nc",
            r"\|\s*sh",
            r"\|\s*bash",
            r"&&\s*rm",
            r"&&\s*wget",
            r"&&\s*curl",
            r"`.*`",
            r"\$\(.*\)"
        ]
        
        self.suspicious_user_agents = [
            r"sqlmap",
            r"nmap",
            r"nikto",
            r"dirb",
            r"dirbuster",
            r"gobuster",
            r"wfuzz",
            r"burp",
            r"nessus",
            r"openvas",
            r"acunetix",
            r"havij",
            r"pangolin",
            r"paros",
            r"webscarab",
            r"w3af",
            r"skipfish",
            r"arachni",
            r"vega",
            r"zap",
            r"python-requests",
            r"curl",
            r"wget",
            r"masscan",
            r"zgrab"
        ]
        
        # Stockage des événements et profiles
        self.security_events: deque = deque(maxlen=10000)
        self.ip_profiles: Dict[str, IPProfile] = {}
        self.blocked_ips: Set[str] = set()
        self.whitelisted_ips: Set[str] = set()
        
        # Seuils de détection
        self.thresholds = {
            "failed_auth_attempts": 5,
            "failed_auth_window_minutes": 10,
            "requests_per_minute": 100,
            "requests_per_hour": 1000,
            "suspicious_score_threshold": 0.7,
            "unique_endpoints_threshold": 50,
            "unusual_activity_threshold": 0.8
        }
        
        # Statistiques
        self.stats = {
            "total_events": 0,
            "blocked_attacks": 0,
            "false_positives": 0,
            "active_threats": 0,
            "last_scan": None
        }
    
    def analyze_request(self, 
                       ip_address: str,
                       endpoint: str,
                       method: str,
                       user_agent: str,
                       payload: Optional[str] = None,
                       user_id: Optional[int] = None,
                       headers: Optional[Dict[str, str]] = None) -> List[SecurityEvent]:
        """Analyse une requête pour détecter les menaces"""
        
        events = []
        now = datetime.now(timezone.utc)
        
        # Mettre à jour le profil IP
        self._update_ip_profile(ip_address, endpoint, user_agent)
        
        # Vérifier si l'IP est bloquée
        if ip_address in self.blocked_ips:
            events.append(SecurityEvent(
                timestamp=now,
                ip_address=ip_address,
                user_id=user_id,
                attack_type=AttackType.UNUSUAL_ACTIVITY,
                threat_level=ThreatLevel.HIGH,
                details={"reason": "IP blocked"},
                confidence=1.0,
                endpoint=endpoint,
                user_agent=user_agent,
                blocked=True
            ))
        
        # Analyser les patterns d'attaque
        if payload:
            # Détection SQL Injection
            sql_confidence = self._check_sql_injection(payload)
            if sql_confidence > 0.5:
                events.append(SecurityEvent(
                    timestamp=now,
                    ip_address=ip_address,
                    user_id=user_id,
                    attack_type=AttackType.SQL_INJECTION,
                    threat_level=ThreatLevel.HIGH if sql_confidence > 0.8 else ThreatLevel.MEDIUM,
                    details={"patterns_matched": self._get_matched_patterns(payload, self.sql_injection_patterns)},
                    confidence=sql_confidence,
                    endpoint=endpoint,
                    user_agent=user_agent,
                    payload=payload
                ))
            
            # Détection XSS
            xss_confidence = self._check_xss(payload)
            if xss_confidence > 0.5:
                events.append(SecurityEvent(
                    timestamp=now,
                    ip_address=ip_address,
                    user_id=user_id,
                    attack_type=AttackType.XSS,
                    threat_level=ThreatLevel.HIGH if xss_confidence > 0.8 else ThreatLevel.MEDIUM,
                    details={"patterns_matched": self._get_matched_patterns(payload, self.xss_patterns)},
                    confidence=xss_confidence,
                    endpoint=endpoint,
                    user_agent=user_agent,
                    payload=payload
                ))
            
            # Détection Directory Traversal
            traversal_confidence = self._check_directory_traversal(payload)
            if traversal_confidence > 0.5:
                events.append(SecurityEvent(
                    timestamp=now,
                    ip_address=ip_address,
                    user_id=user_id,
                    attack_type=AttackType.DIRECTORY_TRAVERSAL,
                    threat_level=ThreatLevel.MEDIUM,
                    details={"patterns_matched": self._get_matched_patterns(payload, self.directory_traversal_patterns)},
                    confidence=traversal_confidence,
                    endpoint=endpoint,
                    user_agent=user_agent,
                    payload=payload
                ))
            
            # Détection Command Injection
            cmd_confidence = self._check_command_injection(payload)
            if cmd_confidence > 0.5:
                events.append(SecurityEvent(
                    timestamp=now,
                    ip_address=ip_address,
                    user_id=user_id,
                    attack_type=AttackType.COMMAND_INJECTION,
                    threat_level=ThreatLevel.HIGH,
                    details={"patterns_matched": self._get_matched_patterns(payload, self.command_injection_patterns)},
                    confidence=cmd_confidence,
                    endpoint=endpoint,
                    user_agent=user_agent,
                    payload=payload
                ))
        
        # Vérifier User-Agent suspect
        ua_confidence = self._check_suspicious_user_agent(user_agent)
        if ua_confidence > 0.7:
            events.append(SecurityEvent(
                timestamp=now,
                ip_address=ip_address,
                user_id=user_id,
                attack_type=AttackType.SUSPICIOUS_USER_AGENT,
                threat_level=ThreatLevel.MEDIUM,
                details={"user_agent": user_agent},
                confidence=ua_confidence,
                endpoint=endpoint,
                user_agent=user_agent
            ))
        
        # Vérifier les patterns comportementaux
        behavioral_events = self._check_behavioral_patterns(ip_address, endpoint, user_id)
        events.extend(behavioral_events)
        
        # Enregistrer les événements
        for event in events:
            self.security_events.append(event)
            self.stats["total_events"] += 1
            
            if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                self.stats["active_threats"] += 1
            
            # Bloquer automatiquement les menaces critiques
            if event.threat_level == ThreatLevel.CRITICAL:
                self.block_ip(ip_address)
                event.blocked = True
                self.stats["blocked_attacks"] += 1
        
        return events
    
    def _update_ip_profile(self, ip_address: str, endpoint: str, user_agent: str):
        """Met à jour le profil comportemental d'une IP"""
        
        now = datetime.now(timezone.utc)
        
        if ip_address not in self.ip_profiles:
            self.ip_profiles[ip_address] = IPProfile(
                ip_address=ip_address,
                first_seen=now,
                last_seen=now
            )
        
        profile = self.ip_profiles[ip_address]
        profile.update_activity(endpoint, user_agent)
        
        # Calculer le score de suspicion
        profile.suspicious_score = self._calculate_suspicious_score(profile)
    
    def _calculate_suspicious_score(self, profile: IPProfile) -> float:
        """Calcule le score de suspicion d'une IP"""
        
        score = 0.0
        
        # Ratio d'échecs d'authentification
        if profile.failed_auth_count > 0:
            auth_ratio = profile.failed_auth_count / (profile.failed_auth_count + profile.successful_auth_count + 1)
            score += auth_ratio * 0.3
        
        # Nombre d'endpoints uniques accédés
        if len(profile.endpoints_accessed) > self.thresholds["unique_endpoints_threshold"]:
            score += 0.2
        
        # Diversité des User-Agents
        if len(profile.user_agents) > 10:
            score += 0.1
        
        # Activité récente intensive
        now = datetime.now(timezone.utc)
        if profile.last_seen and (now - profile.last_seen).total_seconds() < 3600:
            if profile.request_count > self.thresholds["requests_per_hour"]:
                score += 0.3
        
        # Patterns suspects dans les User-Agents
        for ua in profile.user_agents:
            if self._check_suspicious_user_agent(ua) > 0.5:
                score += 0.2
                break
        
        return min(score, 1.0)
    
    def _check_sql_injection(self, payload: str) -> float:
        """Vérifie la présence de patterns SQL Injection"""
        return self._check_patterns(payload, self.sql_injection_patterns)
    
    def _check_xss(self, payload: str) -> float:
        """Vérifie la présence de patterns XSS"""
        return self._check_patterns(payload, self.xss_patterns)
    
    def _check_directory_traversal(self, payload: str) -> float:
        """Vérifie la présence de patterns Directory Traversal"""
        return self._check_patterns(payload, self.directory_traversal_patterns)
    
    def _check_command_injection(self, payload: str) -> float:
        """Vérifie la présence de patterns Command Injection"""
        return self._check_patterns(payload, self.command_injection_patterns)
    
    def _check_suspicious_user_agent(self, user_agent: str) -> float:
        """Vérifie si le User-Agent est suspect"""
        return self._check_patterns(user_agent, self.suspicious_user_agents)
    
    def _check_patterns(self, text: str, patterns: List[str]) -> float:
        """Vérifie la présence de patterns dans le texte"""
        
        if not text:
            return 0.0
        
        text_lower = text.lower()
        matches = 0
        
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                matches += 1
        
        # Confiance basée sur le nombre de patterns qui matchent
        confidence = min(matches / len(patterns) * 2, 1.0)
        return confidence
    
    def _get_matched_patterns(self, text: str, patterns: List[str]) -> List[str]:
        """Retourne les patterns qui matchent dans le texte"""
        
        if not text:
            return []
        
        text_lower = text.lower()
        matched = []
        
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                matched.append(pattern)
        
        return matched
    
    def _check_behavioral_patterns(self, 
                                  ip_address: str, 
                                  endpoint: str, 
                                  user_id: Optional[int]) -> List[SecurityEvent]:
        """Vérifie les patterns comportementaux suspects"""
        
        events = []
        now = datetime.now(timezone.utc)
        
        profile = self.ip_profiles.get(ip_address)
        if not profile:
            return events
        
        # Détection de brute force
        if profile.failed_auth_count >= self.thresholds["failed_auth_attempts"]:
            time_window = now - timedelta(minutes=self.thresholds["failed_auth_window_minutes"])
            if profile.last_seen >= time_window:
                events.append(SecurityEvent(
                    timestamp=now,
                    ip_address=ip_address,
                    user_id=user_id,
                    attack_type=AttackType.BRUTE_FORCE,
                    threat_level=ThreatLevel.HIGH,
                    details={
                        "failed_attempts": profile.failed_auth_count,
                        "window_minutes": self.thresholds["failed_auth_window_minutes"]
                    },
                    confidence=0.9,
                    endpoint=endpoint,
                    user_agent=list(profile.user_agents)[0] if profile.user_agents else ""
                ))
        
        # Détection d'abus de rate limiting
        if profile.request_count > self.thresholds["requests_per_minute"]:
            events.append(SecurityEvent(
                timestamp=now,
                ip_address=ip_address,
                user_id=user_id,
                attack_type=AttackType.RATE_LIMIT_ABUSE,
                threat_level=ThreatLevel.MEDIUM,
                details={
                    "request_count": profile.request_count,
                    "threshold": self.thresholds["requests_per_minute"]
                },
                confidence=0.8,
                endpoint=endpoint,
                user_agent=list(profile.user_agents)[0] if profile.user_agents else ""
            ))
        
        # Détection d'activité inhabituelle
        if profile.suspicious_score > self.thresholds["suspicious_score_threshold"]:
            events.append(SecurityEvent(
                timestamp=now,
                ip_address=ip_address,
                user_id=user_id,
                attack_type=AttackType.UNUSUAL_ACTIVITY,
                threat_level=ThreatLevel.MEDIUM,
                details={
                    "suspicious_score": profile.suspicious_score,
                    "threshold": self.thresholds["suspicious_score_threshold"],
                    "unique_endpoints": len(profile.endpoints_accessed),
                    "unique_user_agents": len(profile.user_agents)
                },
                confidence=profile.suspicious_score,
                endpoint=endpoint,
                user_agent=list(profile.user_agents)[0] if profile.user_agents else ""
            ))
        
        return events
    
    def block_ip(self, ip_address: str) -> None:
        """Bloque une adresse IP"""
        self.blocked_ips.add(ip_address)
        logger.warning(f"IP bloquée: {ip_address}")
    
    def unblock_ip(self, ip_address: str) -> None:
        """Débloque une adresse IP"""
        self.blocked_ips.discard(ip_address)
        logger.info(f"IP débloquée: {ip_address}")
    
    def whitelist_ip(self, ip_address: str) -> None:
        """Ajoute une IP à la whitelist"""
        self.whitelisted_ips.add(ip_address)
        logger.info(f"IP ajoutée à la whitelist: {ip_address}")
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Vérifie si une IP est bloquée"""
        return ip_address in self.blocked_ips
    
    def is_ip_whitelisted(self, ip_address: str) -> bool:
        """Vérifie si une IP est en whitelist"""
        return ip_address in self.whitelisted_ips
    
    def get_security_events(self, 
                           limit: int = 100,
                           threat_level: Optional[ThreatLevel] = None,
                           attack_type: Optional[AttackType] = None,
                           ip_address: Optional[str] = None) -> List[SecurityEvent]:
        """Récupère les événements de sécurité avec filtres"""
        
        events = list(self.security_events)
        
        # Filtrer par niveau de menace
        if threat_level:
            events = [e for e in events if e.threat_level == threat_level]
        
        # Filtrer par type d'attaque
        if attack_type:
            events = [e for e in events if e.attack_type == attack_type]
        
        # Filtrer par IP
        if ip_address:
            events = [e for e in events if e.ip_address == ip_address]
        
        # Trier par timestamp décroissant
        events.sort(key=lambda x: x.timestamp, reverse=True)
        
        return events[:limit]
    
    def get_ip_profile(self, ip_address: str) -> Optional[IPProfile]:
        """Récupère le profil d'une IP"""
        return self.ip_profiles.get(ip_address)
    
    def get_top_threats(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Récupère les IP les plus menaçantes"""
        
        threats = []
        for ip, profile in self.ip_profiles.items():
            if profile.suspicious_score > 0.5:
                threats.append((ip, profile.suspicious_score))
        
        threats.sort(key=lambda x: x[1], reverse=True)
        return threats[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du système"""
        
        now = datetime.now(timezone.utc)
        
        # Calculer les événements récents
        recent_events = [e for e in self.security_events 
                        if e.timestamp >= now - timedelta(hours=24)]
        
        threat_counts = defaultdict(int)
        for event in recent_events:
            threat_counts[event.threat_level.value] += 1
        
        return {
            **self.stats,
            "blocked_ips_count": len(self.blocked_ips),
            "whitelisted_ips_count": len(self.whitelisted_ips),
            "tracked_ips_count": len(self.ip_profiles),
            "recent_events_24h": len(recent_events),
            "threat_level_distribution": dict(threat_counts),
            "top_threats": self.get_top_threats(5)
        }
    
    async def cleanup_old_data(self, retention_days: int = 30) -> None:
        """Nettoie les anciennes données"""
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        # Nettoyer les profils IP anciens
        old_ips = []
        for ip, profile in self.ip_profiles.items():
            if profile.last_seen < cutoff_date:
                old_ips.append(ip)
        
        for ip in old_ips:
            if ip not in self.blocked_ips and ip not in self.whitelisted_ips:
                del self.ip_profiles[ip]
        
        logger.info(f"Nettoyage terminé: {len(old_ips)} profils IP supprimés")


# Instance globale
ids_instance = None

def get_intrusion_detection_system() -> IntrusionDetectionSystem:
    """Obtient l'instance du système de détection d'intrusion"""
    global ids_instance
    if ids_instance is None:
        ids_instance = IntrusionDetectionSystem()
    return ids_instance
