# 🔐 SÉCURITÉ HARDENING - WakeDock

**Priorité: 🟡 MOYENNE-HAUTE**  
**Timeline: 3-4 semaines**  
**Équipe: Security Engineer + DevSecOps + Backend Dev + Frontend Dev**

## 📋 Vue d'Ensemble

Ce document détaille le durcissement sécuritaire complet de la plateforme WakeDock. Suite à l'audit sécuritaire, plusieurs vulnérabilités et faiblesses ont été identifiées nécessitant un hardening immédiat pour atteindre les standards de sécurité enterprise.

---

## 🎯 OBJECTIFS SÉCURITÉ

### 🛡️ Standards de Conformité
- **OWASP Top 10 2023** - Compliance complète
- **NIST Cybersecurity Framework** - Core functions
- **CIS Docker Benchmark** - Level 1 compliance
- **SOC 2 Type II** - Préparation audit

### 📊 Métriques Sécurité Cibles

```yaml
Security Metrics:
  - Vulnerability Scan: 0 Critical, <5 High
  - Authentication: MFA obligatoire admin
  - Encryption: TLS 1.3 minimum partout
  - Access Control: RBAC granulaire
  - Audit Logging: 100% actions critiques
  - Secret Management: 0 secrets hardcodés
  - Container Security: CIS Level 1 compliant
  - Network Security: Zero-trust architecture
```

---

## 🚨 VULNÉRABILITÉS CRITIQUES IDENTIFIÉES

### 1. Authentication & Session Management

**Issues Actuelles:**
- 2FA temporairement désactivée (critique)
- Session timeout non configuré
- Pas de rate limiting login
- JWT sans rotation automatique

**Solutions Immédiates:**

```python
# src/wakedock/security/auth/mfa.py
import pyotp
import qrcode
from io import BytesIO
import base64
from typing import Optional, Tuple

class MFAManager:
    """Gestionnaire Multi-Factor Authentication"""
    
    def __init__(self, app_name: str = "WakeDock"):
        self.app_name = app_name
        self.issuer_name = "WakeDock Platform"
    
    def generate_secret(self) -> str:
        """Génère un secret TOTP unique"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """Génère QR code pour configuration app authenticator"""
        
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=self.issuer_name
        )
        
        # Génération QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        # Conversion en base64 pour embedding
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def verify_token(self, secret: str, token: str, window: int = 1) -> bool:
        """Vérifie token TOTP avec fenêtre de tolérance"""
        
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=window)
    
    def get_backup_codes(self, count: int = 8) -> List[str]:
        """Génère codes de récupération"""
        
        import secrets
        import string
        
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) 
                          for _ in range(8))
            # Format: XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        
        return codes

# Enhanced Authentication Store
class SecureAuthService:
    """Service d'authentification sécurisé"""
    
    def __init__(self, db, cache, mfa_manager):
        self.db = db
        self.cache = cache
        self.mfa = mfa_manager
        self.login_attempts = {}  # Rate limiting
    
    async def authenticate(
        self, 
        username: str, 
        password: str,
        mfa_token: Optional[str] = None,
        user_agent: str = None,
        ip_address: str = None
    ) -> Tuple[bool, Optional[dict], Optional[str]]:
        """Authentification sécurisée avec MFA"""
        
        # 1. Rate limiting
        if not await self._check_rate_limit(username, ip_address):
            await self._log_security_event("rate_limit_exceeded", {
                "username": username,
                "ip_address": ip_address
            })
            return False, None, "Too many login attempts"
        
        # 2. Validation credentials
        user = await self._validate_credentials(username, password)
        if not user:
            await self._record_failed_attempt(username, ip_address)
            return False, None, "Invalid credentials"
        
        # 3. Vérification MFA si activé
        if user.mfa_enabled:
            if not mfa_token:
                return False, {"requires_mfa": True}, "MFA required"
            
            if not self.mfa.verify_token(user.mfa_secret, mfa_token):
                await self._record_failed_attempt(username, ip_address, "mfa_failed")
                return False, None, "Invalid MFA token"
        
        # 4. Génération session sécurisée
        session_data = await self._create_secure_session(user, ip_address, user_agent)
        
        # 5. Audit logging
        await self._log_security_event("successful_login", {
            "user_id": user.id,
            "username": username,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "mfa_used": user.mfa_enabled
        })
        
        return True, session_data, None
    
    async def _check_rate_limit(self, username: str, ip_address: str) -> bool:
        """Rate limiting avancé"""
        
        current_time = time.time()
        
        # Rate limit par username (5 tentatives / 15 minutes)
        user_key = f"login_attempts:user:{username}"
        user_attempts = await self.cache.get(user_key) or []
        user_attempts = [t for t in user_attempts if current_time - t < 900]  # 15 min
        
        if len(user_attempts) >= 5:
            return False
        
        # Rate limit par IP (10 tentatives / 15 minutes)
        ip_key = f"login_attempts:ip:{ip_address}"
        ip_attempts = await self.cache.get(ip_key) or []
        ip_attempts = [t for t in ip_attempts if current_time - t < 900]
        
        if len(ip_attempts) >= 10:
            return False
        
        return True
    
    async def _create_secure_session(
        self, 
        user: User, 
        ip_address: str, 
        user_agent: str
    ) -> dict:
        """Création session sécurisée avec rotation JWT"""
        
        session_id = secrets.token_urlsafe(32)
        
        # JWT avec courte durée de vie
        access_token = self._generate_jwt(user, session_id, expires_minutes=15)
        refresh_token = self._generate_refresh_token(user, session_id)
        
        # Session tracking en DB
        session = UserSession(
            id=session_id,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=8),
            is_active=True
        )
        
        await self.db.add(session)
        await self.db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "session_id": session_id,
            "expires_in": 900,  # 15 minutes
            "user": user.to_safe_dict()
        }
```

---

### 2. Secrets Management

**Problème:** Variables d'environnement en clair, pas de rotation

**Solution - HashiCorp Vault Integration:**

```python
# src/wakedock/security/secrets/vault.py
import hvac
import os
from typing import Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class SecretConfig:
    """Configuration secret Vault"""
    path: str
    mount_point: str = "secret"
    auto_rotate: bool = False
    rotate_interval: int = 86400  # 24h

class VaultSecretManager:
    """Gestionnaire secrets avec HashiCorp Vault"""
    
    def __init__(self, vault_url: str, vault_token: str = None):
        self.client = hvac.Client(url=vault_url)
        
        # Authentication automatique
        if vault_token:
            self.client.token = vault_token
        else:
            # Authentification via role Kubernetes/AWS
            self._authenticate_auto()
        
        # Vérification santé Vault
        if not self.client.sys.is_sealed():
            raise Exception("Vault is sealed")
    
    def _authenticate_auto(self):
        """Auto-authentication basée sur l'environnement"""
        
        # Kubernetes Service Account
        if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/token"):
            with open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r") as f:
                jwt = f.read()
            
            role = os.environ.get("VAULT_ROLE", "wakedock")
            
            response = self.client.auth.kubernetes.login(
                role=role,
                jwt=jwt
            )
            self.client.token = response['auth']['client_token']
        
        # AWS IAM (pour deployment AWS)
        elif os.environ.get("AWS_ROLE_ARN"):
            self.client.auth.aws.iam_login(
                access_key=os.environ["AWS_ACCESS_KEY_ID"],
                secret_key=os.environ["AWS_SECRET_ACCESS_KEY"],
                role=os.environ.get("VAULT_AWS_ROLE", "wakedock")
            )
    
    async def get_secret(self, path: str, key: str = None) -> Any:
        """Récupération secret sécurisé"""
        
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point="secret"
            )
            
            secrets = response['data']['data']
            
            if key:
                return secrets.get(key)
            return secrets
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret {path}: {e}")
            raise
    
    async def set_secret(
        self, 
        path: str, 
        secrets: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ):
        """Stockage secret sécurisé"""
        
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secrets,
                mount_point="secret"
            )
            
            # Metadata personnalisée
            if metadata:
                self.client.secrets.kv.v2.update_metadata(
                    path=path,
                    mount_point="secret",
                    **metadata
                )
                
        except Exception as e:
            logger.error(f"Failed to store secret {path}: {e}")
            raise
    
    async def rotate_secret(self, path: str, generator_func: callable):
        """Rotation automatique de secret"""
        
        try:
            # Génération nouveau secret
            new_secret = await generator_func()
            
            # Stockage avec versioning
            await self.set_secret(path, new_secret, {
                "rotated_at": datetime.utcnow().isoformat(),
                "rotation_source": "automatic"
            })
            
            logger.info(f"Secret rotated successfully: {path}")
            
        except Exception as e:
            logger.error(f"Secret rotation failed for {path}: {e}")
            raise

# Configuration loader sécurisé
class SecureConfigLoader:
    """Chargeur configuration sécurisé"""
    
    def __init__(self, vault_manager: VaultSecretManager):
        self.vault = vault_manager
        self._config_cache = {}
    
    async def load_database_config(self) -> dict:
        """Configuration base de données depuis Vault"""
        
        db_secrets = await self.vault.get_secret("wakedock/database")
        
        return {
            "database_url": f"postgresql://{db_secrets['username']}:{db_secrets['password']}@{db_secrets['host']}/{db_secrets['database']}",
            "pool_size": 20,
            "max_overflow": 30,
            "pool_recycle": 3600
        }
    
    async def load_jwt_config(self) -> dict:
        """Configuration JWT depuis Vault"""
        
        jwt_secrets = await self.vault.get_secret("wakedock/jwt")
        
        return {
            "secret_key": jwt_secrets["secret_key"],
            "algorithm": "HS256",
            "access_token_expire_minutes": 15,
            "refresh_token_expire_days": 7
        }
    
    async def load_external_api_keys(self) -> dict:
        """Clés API externes depuis Vault"""
        
        api_secrets = await self.vault.get_secret("wakedock/external-apis")
        
        return {
            "docker_registry_token": api_secrets.get("docker_registry"),
            "monitoring_api_key": api_secrets.get("monitoring"),
            "notification_webhook": api_secrets.get("slack_webhook")
        }
```

---

### 3. Network Security & Zero Trust

```python
# src/wakedock/security/network/zero_trust.py
from typing import List, Dict, Optional
from ipaddress import IPv4Network, IPv4Address
import geoip2.database
from user_agents import parse

class NetworkSecurityManager:
    """Gestionnaire sécurité réseau Zero Trust"""
    
    def __init__(self):
        self.trusted_networks = [
            IPv4Network("10.0.0.0/8"),      # Private networks
            IPv4Network("172.16.0.0/12"),
            IPv4Network("192.168.0.0/16")
        ]
        
        self.blocked_countries = [
            "CN", "RU", "KP", "IR"  # Pays à risque élevé
        ]
        
        # GeoIP database pour géolocalisation
        try:
            self.geoip_reader = geoip2.database.Reader('/usr/share/GeoIP/GeoLite2-Country.mmdb')
        except:
            self.geoip_reader = None
            logger.warning("GeoIP database not available")
    
    async def validate_request_security(
        self, 
        ip_address: str,
        user_agent: str,
        headers: Dict[str, str],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Validation sécurité complète d'une requête"""
        
        security_score = 100
        warnings = []
        blocks = []
        
        # 1. Validation IP et géolocalisation
        ip_analysis = await self._analyze_ip_address(ip_address)
        security_score -= ip_analysis["risk_score"]
        warnings.extend(ip_analysis["warnings"])
        blocks.extend(ip_analysis["blocks"])
        
        # 2. Analyse User-Agent
        ua_analysis = self._analyze_user_agent(user_agent)
        security_score -= ua_analysis["risk_score"]
        warnings.extend(ua_analysis["warnings"])
        
        # 3. Validation headers
        header_analysis = self._analyze_headers(headers)
        security_score -= header_analysis["risk_score"]
        warnings.extend(header_analysis["warnings"])
        
        # 4. Comportement utilisateur (si connecté)
        if user_id:
            behavior_analysis = await self._analyze_user_behavior(user_id, ip_address)
            security_score -= behavior_analysis["risk_score"]
            warnings.extend(behavior_analysis["warnings"])
        
        # Décision finale
        allow_request = len(blocks) == 0 and security_score > 30
        
        return {
            "allow": allow_request,
            "security_score": max(0, security_score),
            "warnings": warnings,
            "blocks": blocks,
            "require_additional_auth": security_score < 70
        }
    
    async def _analyze_ip_address(self, ip_address: str) -> Dict[str, Any]:
        """Analyse sécurité adresse IP"""
        
        risk_score = 0
        warnings = []
        blocks = []
        
        try:
            ip = IPv4Address(ip_address)
            
            # Vérification liste noire IP
            if await self._is_ip_blacklisted(ip_address):
                blocks.append("IP address is blacklisted")
                risk_score += 100
            
            # Géolocalisation
            if self.geoip_reader:
                try:
                    response = self.geoip_reader.country(ip_address)
                    country_code = response.country.iso_code
                    
                    if country_code in self.blocked_countries:
                        blocks.append(f"Requests from {country_code} are blocked")
                        risk_score += 50
                    
                    # Log géolocalisation pour audit
                    logger.info(f"Request from {country_code}: {ip_address}")
                    
                except Exception as e:
                    warnings.append("Could not determine geolocation")
            
            # Vérification réseaux privés
            is_private = any(ip in network for network in self.trusted_networks)
            if not is_private:
                risk_score += 10
                warnings.append("Request from public IP")
            
            # Check proxy/VPN/Tor
            if await self._is_proxy_or_vpn(ip_address):
                risk_score += 25
                warnings.append("Request appears to be from proxy/VPN")
                
        except ValueError:
            warnings.append("Invalid IP address format")
            risk_score += 20
        
        return {
            "risk_score": risk_score,
            "warnings": warnings,
            "blocks": blocks
        }
    
    def _analyze_user_agent(self, user_agent: str) -> Dict[str, Any]:
        """Analyse User-Agent pour détection bot/anomalie"""
        
        risk_score = 0
        warnings = []
        
        if not user_agent:
            warnings.append("Missing User-Agent header")
            risk_score += 20
            return {"risk_score": risk_score, "warnings": warnings}
        
        # Parse User-Agent
        parsed_ua = parse(user_agent)
        
        # Détection bots connus
        bot_signatures = [
            "bot", "crawler", "spider", "scraper", "curl", "wget", "python-requests"
        ]
        
        if any(bot in user_agent.lower() for bot in bot_signatures):
            warnings.append("Bot or automated tool detected")
            risk_score += 15
        
        # Vérification navigateur/OS cohérence
        if parsed_ua.browser.family == "Other" and parsed_ua.os.family == "Other":
            warnings.append("Unusual or spoofed User-Agent")
            risk_score += 10
        
        # User-Agents trop anciens (sécurité)
        if parsed_ua.browser.version and len(parsed_ua.browser.version) >= 2:
            major_version = int(parsed_ua.browser.version[0])
            
            # Chrome < 90, Firefox < 85, Safari < 14
            if ((parsed_ua.browser.family == "Chrome" and major_version < 90) or
                (parsed_ua.browser.family == "Firefox" and major_version < 85) or
                (parsed_ua.browser.family == "Safari" and major_version < 14)):
                warnings.append("Outdated browser version detected")
                risk_score += 5
        
        return {"risk_score": risk_score, "warnings": warnings}
    
    async def _analyze_user_behavior(
        self, 
        user_id: int, 
        ip_address: str
    ) -> Dict[str, Any]:
        """Analyse comportementale utilisateur"""
        
        risk_score = 0
        warnings = []
        
        # Récupérer historique connexions utilisateur (7 derniers jours)
        recent_sessions = await self._get_user_recent_sessions(user_id, days=7)
        
        if recent_sessions:
            # Vérification changement géographique brusque
            known_ips = [session.ip_address for session in recent_sessions]
            
            if ip_address not in known_ips:
                # Nouvelle IP - vérifier distance géographique
                distance = await self._calculate_geographic_distance(
                    known_ips[-1], ip_address
                )
                
                if distance > 1000:  # > 1000km
                    warnings.append("Login from unusual geographic location")
                    risk_score += 20
                
                # Nouvelle IP dans courte période
                last_session_time = recent_sessions[-1].created_at
                if (datetime.utcnow() - last_session_time).total_seconds() < 3600:
                    warnings.append("Rapid IP address change detected")
                    risk_score += 15
            
            # Analyse patterns temporels
            session_hours = [session.created_at.hour for session in recent_sessions]
            current_hour = datetime.utcnow().hour
            
            # Connexion à heure inhabituelle
            if current_hour not in session_hours and len(session_hours) > 5:
                warnings.append("Login at unusual time")
                risk_score += 10
        
        return {"risk_score": risk_score, "warnings": warnings}
```

---

### 4. Container Security Hardening

```dockerfile
# Dockerfile sécurisé - WakeDock Backend
FROM python:3.11-slim as base

# Security: Utiliser des sources officielles uniquement
ARG DEBIAN_FRONTEND=noninteractive

# Security: Mise à jour sécurité système
RUN apt-get update && apt-get install -y \
    # Packages sécurisés minimaux
    gcc \
    libpq-dev \
    # Security: supprimer packages non nécessaires
    && apt-get purge -y --auto-remove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    # Security: supprimer caches
    && rm -rf /tmp/* /var/tmp/*

# Security: Utilisateur non-root dédié
RUN groupadd -r wakedock && useradd -r -g wakedock \
    --home-dir=/app \
    --shell=/sbin/nologin \
    wakedock

# Security: Répertoires avec permissions restrictives
WORKDIR /app
RUN chown wakedock:wakedock /app

# Stage production sécurisé
FROM base as production

# Security: Copier avec permissions appropriées
COPY --chown=wakedock:wakedock --from=dependencies /app/.venv /app/.venv
COPY --chown=wakedock:wakedock src/ src/
COPY --chown=wakedock:wakedock alembic/ alembic/
COPY --chown=wakedock:wakedock alembic.ini .

# Security: Variables environnement sécurisées
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Security: Désactiver fonctionnalités Python dangereuses
    PYTHONHASHSEED=random \
    PYTHONNOUSERSITE=1 \
    # Security: Logging sécurisé
    PYTHONPATH=/app/src

# Security: Switch to non-root user
USER wakedock

# Security: Health check sans privilèges
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Security: Commande finale sécurisée
CMD ["uvicorn", "wakedock.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--access-log", \
     "--no-server-header"]

# Security: Labels de sécurité
LABEL security.scan="enabled" \
      security.vulnerabilities="none" \
      security.compliance="cis-docker-benchmark-1.0"
```

```yaml
# docker-compose.security.yml - Configuration sécurisée
version: '3.8'

services:
  wakedock:
    # Security: Image avec digest pour intégrité
    image: wakedock:latest@sha256:abc123...
    
    # Security: Capabilities minimales
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Pour port 8000 uniquement
    
    # Security: Système de fichiers en lecture seule
    read_only: true
    
    # Security: tmpfs pour écriture temporaire
    tmpfs:
      - /tmp:size=100M,noexec,nosuid,nodev
      - /var/run:size=10M,noexec,nosuid,nodev
    
    # Security: Pas de privilèges
    privileged: false
    user: "1000:1000"  # UID/GID wakedock
    
    # Security: Restrictions ressources
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
          pids: 100  # Limite processus
    
    # Security: Variables d'environnement via secrets
    environment:
      - DATABASE_URL_FILE=/run/secrets/database_url
      - JWT_SECRET_FILE=/run/secrets/jwt_secret
    
    secrets:
      - database_url
      - jwt_secret
    
    # Security: Réseau isolé
    networks:
      - wakedock-internal
    
    # Security: Pas d'accès Docker socket
    # volumes: JAMAIS /var/run/docker.sock

  postgres:
    image: postgres:15-alpine
    
    # Security: Configuration PostgreSQL durcie
    environment:
      - POSTGRES_DB_FILE=/run/secrets/postgres_db
      - POSTGRES_USER_FILE=/run/secrets/postgres_user  
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
      # Security: Paramètres sécurisés
      - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256 --auth-local=scram-sha-256
    
    command: >
      postgres
      -c ssl=on
      -c ssl_cert_file=/var/lib/postgresql/server.crt
      -c ssl_key_file=/var/lib/postgresql/server.key
      -c ssl_ca_file=/var/lib/postgresql/ca.crt
      -c log_statement=all
      -c log_connections=on
      -c log_disconnections=on
      -c log_checkpoints=on
      -c shared_preload_libraries=pg_stat_statements
    
    # Security: Utilisateur non-root
    user: "999:999"
    
    secrets:
      - postgres_db
      - postgres_user
      - postgres_password
      - source: postgres_ssl_cert
        target: /var/lib/postgresql/server.crt
      - source: postgres_ssl_key
        target: /var/lib/postgresql/server.key
        mode: 0600
    
    networks:
      - wakedock-internal

  # Security: Proxy WAF avec ModSecurity
  waf:
    image: owasp/modsecurity-crs:nginx
    
    environment:
      - PARANOIA=2  # Niveau sécurité élevé
      - ANOMALY_INBOUND=5
      - ANOMALY_OUTBOUND=4
      - BLOCKING_PARANOIA=2
    
    volumes:
      - ./security/waf-rules:/etc/modsecurity.d/custom-rules:ro
      - ./security/nginx.conf:/etc/nginx/nginx.conf:ro
    
    ports:
      - "443:443"
      - "80:80"
    
    networks:
      - wakedock-external
      - wakedock-internal
    
    depends_on:
      - wakedock

# Security: Secrets externes (Vault/Kubernetes)
secrets:
  database_url:
    external: true
    name: wakedock_database_url
  jwt_secret:
    external: true
    name: wakedock_jwt_secret
  postgres_db:
    external: true
    name: wakedock_postgres_db
  postgres_user:
    external: true
    name: wakedock_postgres_user
  postgres_password:
    external: true
    name: wakedock_postgres_password
  postgres_ssl_cert:
    external: true
    name: wakedock_postgres_ssl_cert
  postgres_ssl_key:
    external: true
    name: wakedock_postgres_ssl_key

# Security: Réseaux isolés
networks:
  wakedock-external:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.enable_icc: "false"
  
  wakedock-internal:
    driver: bridge
    internal: true  # Pas d'accès Internet
    driver_opts:
      com.docker.network.bridge.enable_icc: "true"
```

---

## 🛡️ AUDIT ET MONITORING SÉCURITÉ

### Security Event Logging

```python
# src/wakedock/security/audit/logger.py
import json
import asyncio
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime

class SecurityEventType(Enum):
    """Types d'événements sécurité"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    MFA_SUCCESS = "mfa_success"
    MFA_FAILURE = "mfa_failure"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS = "data_access"
    CONFIGURATION_CHANGE = "configuration_change"
    SECRET_ACCESS = "secret_access"
    API_ABUSE = "api_abuse"
    SECURITY_VIOLATION = "security_violation"

class SecurityAuditLogger:
    """Logger audit sécurité centralisé"""
    
    def __init__(self, siem_endpoint: Optional[str] = None):
        self.siem_endpoint = siem_endpoint
        self.local_buffer = []
        self.buffer_size = 1000
    
    async def log_security_event(
        self,
        event_type: SecurityEventType,
        details: Dict[str, Any],
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: str = "info"
    ):
        """Log événement sécurité avec format standardisé"""
        
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "severity": severity,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details,
            "source": "wakedock",
            "version": "1.0"
        }
        
        # Log local
        logger.info(f"SECURITY_EVENT: {json.dumps(event)}")
        
        # Buffer pour SIEM
        self.local_buffer.append(event)
        
        if len(self.local_buffer) >= self.buffer_size:
            await self._flush_to_siem()
        
        # Alerting immédiat pour événements critiques
        if severity in ["critical", "high"]:
            await self._send_immediate_alert(event)
    
    async def _flush_to_siem(self):
        """Envoi batch vers SIEM externe"""
        
        if not self.siem_endpoint or not self.local_buffer:
            return
        
        try:
            # Envoi vers SIEM (Splunk, ELK, etc.)
            async with aiohttp.ClientSession() as session:
                await session.post(
                    self.siem_endpoint,
                    json={"events": self.local_buffer},
                    headers={"Content-Type": "application/json"}
                )
            
            self.local_buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to send security events to SIEM: {e}")
    
    async def _send_immediate_alert(self, event: Dict[str, Any]):
        """Alerte immédiate pour événements critiques"""
        
        alert_message = f"""
        🚨 SECURITY ALERT 🚨
        
        Event: {event['event_type']}
        Severity: {event['severity']}
        User: {event.get('user_id', 'Unknown')}
        IP: {event.get('ip_address', 'Unknown')}
        Time: {event['timestamp']}
        
        Details: {json.dumps(event['details'], indent=2)}
        """
        
        # Notification Slack/Teams/Email
        await self._send_notification(alert_message, event['severity'])

# Middleware audit automatique
class SecurityAuditMiddleware:
    """Middleware audit sécurité automatique"""
    
    def __init__(self, audit_logger: SecurityAuditLogger):
        self.audit_logger = audit_logger
    
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        # Extraction données requête
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        user_id = getattr(request.state, "user_id", None)
        
        try:
            response = await call_next(request)
            
            # Audit routes sensibles
            if self._is_sensitive_route(request.url.path):
                await self.audit_logger.log_security_event(
                    SecurityEventType.DATA_ACCESS,
                    {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "response_time": time.time() - start_time
                    },
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            return response
            
        except HTTPException as e:
            # Audit erreurs d'autorisation
            if e.status_code in [401, 403]:
                await self.audit_logger.log_security_event(
                    SecurityEventType.UNAUTHORIZED_ACCESS,
                    {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": e.status_code,
                        "error": str(e.detail)
                    },
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    severity="warning"
                )
            
            raise
    
    def _is_sensitive_route(self, path: str) -> bool:
        """Identification routes sensibles nécessitant audit"""
        
        sensitive_patterns = [
            "/api/v1/users",
            "/api/v1/auth/",
            "/api/v1/admin/",
            "/api/v1/settings",
            "/api/v1/secrets"
        ]
        
        return any(pattern in path for pattern in sensitive_patterns)
```

---

## 🔒 COMPLIANCE ET TESTS SÉCURITÉ

### Tests Sécurité Automatisés

```python
# tests/security/test_security_compliance.py
import pytest
import asyncio
from httpx import AsyncClient
from wakedock.security.audit.logger import SecurityEventType

class TestSecurityCompliance:
    """Tests conformité sécurité automatisés"""
    
    @pytest.mark.security
    async def test_password_policy_enforcement(self, test_client: AsyncClient):
        """Test politique mots de passe"""
        
        weak_passwords = [
            "123456", "password", "admin", "test", "abc123"
        ]
        
        for weak_password in weak_passwords:
            response = await test_client.post("/api/v1/auth/register", json={
                "username": "testuser",
                "password": weak_password,
                "email": "test@example.com"
            })
            
            assert response.status_code == 400
            assert "password does not meet security requirements" in response.json()["detail"]
    
    @pytest.mark.security
    async def test_rate_limiting_protection(self, test_client: AsyncClient):
        """Test protection rate limiting"""
        
        # Tentatives login multiples
        for i in range(10):
            response = await test_client.post("/api/v1/auth/login", data={
                "username": "nonexistent",
                "password": "wrongpassword"
            })
        
        # 11ème tentative doit être bloquée
        response = await test_client.post("/api/v1/auth/login", data={
            "username": "nonexistent", 
            "password": "wrongpassword"
        })
        
        assert response.status_code == 429
        assert "too many attempts" in response.json()["detail"].lower()
    
    @pytest.mark.security
    async def test_sql_injection_protection(self, test_client: AsyncClient, admin_token):
        """Test protection injection SQL"""
        
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; UNION SELECT * FROM users --"
        ]
        
        for payload in sql_payloads:
            response = await test_client.get(
                f"/api/v1/users?search={payload}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            # Ne doit pas retourner d'erreur interne (500)
            assert response.status_code != 500
            
            # Ne doit pas exposer données sensibles
            if response.status_code == 200:
                assert "password" not in str(response.json())
    
    @pytest.mark.security
    async def test_xss_protection(self, test_client: AsyncClient, admin_token):
        """Test protection XSS"""
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            response = await test_client.post("/api/v1/services", 
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "name": payload,
                    "image": "nginx:latest"
                }
            )
            
            # Payload doit être échappé ou rejeté
            if response.status_code == 201:
                service = response.json()
                assert "<script>" not in service["name"]
                assert "javascript:" not in service["name"]
    
    @pytest.mark.security
    async def test_jwt_security(self, test_client: AsyncClient):
        """Test sécurité JWT"""
        
        # Login valide
        response = await test_client.post("/api/v1/auth/login", data={
            "username": "admin",
            "password": "admin123"
        })
        
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Test token manipulation
        malformed_tokens = [
            token[:-5] + "xxxxx",  # Token modifié
            "fake.jwt.token",       # Token complètement faux
            token + "extra",        # Token avec données ajoutées
        ]
        
        for malformed_token in malformed_tokens:
            response = await test_client.get("/api/v1/auth/me",
                headers={"Authorization": f"Bearer {malformed_token}"}
            )
            
            assert response.status_code == 401
    
    @pytest.mark.security
    async def test_cors_security(self, test_client: AsyncClient):
        """Test configuration CORS sécurisée"""
        
        # Test origins malveillantes
        malicious_origins = [
            "http://evil.com",
            "https://attacker.net",
            "null"
        ]
        
        for origin in malicious_origins:
            response = await test_client.options("/api/v1/health",
                headers={"Origin": origin}
            )
            
            # CORS ne doit pas autoriser ces origins
            assert response.headers.get("Access-Control-Allow-Origin") != origin
    
    @pytest.mark.security
    async def test_security_headers(self, test_client: AsyncClient):
        """Test présence headers sécurité"""
        
        response = await test_client.get("/")
        
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Referrer-Policy",
            "Content-Security-Policy"
        ]
        
        for header in required_headers:
            assert header in response.headers, f"Missing security header: {header}"
        
        # Vérification valeurs
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "unsafe-inline" not in response.headers.get("Content-Security-Policy", "")

# Tests pénétration automatisés
class TestPenetrationTesting:
    """Tests pénétration automatisés"""
    
    @pytest.mark.security
    @pytest.mark.slow
    async def test_directory_traversal(self, test_client: AsyncClient):
        """Test attaques directory traversal"""
        
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc//passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        for payload in traversal_payloads:
            response = await test_client.get(f"/api/v1/files/{payload}")
            
            # Ne doit jamais retourner contenu système
            assert response.status_code in [400, 403, 404]
            if response.status_code == 200:
                content = response.text.lower()
                assert "root:" not in content
                assert "administrator" not in content
    
    @pytest.mark.security
    async def test_command_injection(self, test_client: AsyncClient, admin_token):
        """Test injection commandes système"""
        
        command_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`",
            "$(cat /etc/hosts)"
        ]
        
        for payload in command_payloads:
            response = await test_client.post("/api/v1/services",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "name": f"test{payload}",
                    "image": "nginx:latest"
                }
            )
            
            # Commande ne doit pas être exécutée
            if response.status_code == 201:
                # Vérifier que le service n'a pas exécuté de commande
                service = response.json()
                assert "root" not in str(service)
                assert "etc" not in str(service)
```

---

## 🚀 PLAN D'EXÉCUTION SÉCURITÉ

### Phase 1 - Authentification & Secrets (Semaine 1-2)
- [ ] Implémentation MFA TOTP avec backup codes
- [ ] Integration HashiCorp Vault pour secrets
- [ ] Rate limiting avancé sur authentification
- [ ] Session management sécurisé avec rotation JWT

### Phase 2 - Network Security (Semaine 2-3)
- [ ] Zero Trust network validation
- [ ] WAF avec ModSecurity/OWASP CRS
- [ ] Container security hardening
- [ ] TLS 1.3 partout avec certificates auto-rotation

### Phase 3 - Monitoring & Compliance (Semaine 3-4)
- [ ] Security audit logging complet
- [ ] SIEM integration et alerting
- [ ] Tests sécurité automatisés en CI/CD
- [ ] Vulnerability scanning continu

### Phase 4 - Documentation & Training (Semaine 4)
- [ ] Runbooks sécurité et incident response
- [ ] Security awareness documentation
- [ ] Penetration testing complet
- [ ] Compliance audit préparation

---

## 📊 MÉTRIQUES SÉCURITÉ

```yaml
Security KPIs:
  - Mean Time to Detection (MTTD): <5 minutes
  - Mean Time to Response (MTTR): <30 minutes
  - False Positive Rate: <5%
  - Security Test Coverage: >95%
  - Vulnerability Patching: <24h critical, <7d high
  - MFA Adoption Rate: 100% admin, >80% users
  - Security Training Completion: 100% dev team

Compliance Targets:
  - OWASP Top 10: 100% coverage
  - CIS Docker Benchmark: Level 1 compliant
  - SOC 2: Controls implemented
  - GDPR: Privacy by design
```

---

**📞 Contact:** Security Team  
**📅 Review:** Bi-weekly security reviews  
**🚨 Escalation:** CISO pour incidents critiques < 15 minutes**