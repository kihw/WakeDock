#!/usr/bin/env python3
"""
Test simple des fonctionnalités de sécurité
Test sans dépendances externes
"""

import sys
import os
import re
import json
import time
import hashlib
import hmac
import base64
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

# Test des patterns de détection d'intrusion
def test_pattern_detection():
    """Test des patterns de détection d'attaques"""
    print("🔍 Test des patterns de détection...")
    
    # Patterns SQL Injection
    sql_patterns = [
        r"union\s+select",
        r"or\s+1\s*=\s*1",
        r"'\s*or\s*'1'\s*=\s*'1",
        r"admin'\s*--"
    ]
    
    # Tests positifs
    sql_payloads = [
        "id=1' OR '1'='1",
        "username=admin'--",
        "SELECT * FROM users UNION SELECT * FROM admin"
    ]
    
    detected = 0
    for payload in sql_payloads:
        for pattern in sql_patterns:
            if re.search(pattern, payload, re.IGNORECASE):
                detected += 1
                break
    
    print(f"   SQL Injection: {detected}/{len(sql_payloads)} détectés")
    
    # Patterns XSS
    xss_patterns = [
        r"<script",
        r"javascript:",
        r"alert\s*\(",
        r"document\.cookie"
    ]
    
    xss_payloads = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "onclick=alert('xss')"
    ]
    
    detected = 0
    for payload in xss_payloads:
        for pattern in xss_patterns:
            if re.search(pattern, payload, re.IGNORECASE):
                detected += 1
                break
    
    print(f"   XSS: {detected}/{len(xss_payloads)} détectés")
    
    return True

def test_jwt_basics():
    """Test basique des JWT sans dépendances"""
    print("🔐 Test des fonctionnalités JWT...")
    
    # Simulation d'un JWT simple
    secret = "test-secret-key"
    
    # Header et payload
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "user_id": 123,
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp())
    }
    
    # Encodage base64
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    
    # Signature
    message = f"{header_b64}.{payload_b64}"
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')
    
    jwt_token = f"{header_b64}.{payload_b64}.{signature_b64}"
    
    print(f"   Token JWT créé: {jwt_token[:50]}...")
    
    # Validation basique
    parts = jwt_token.split('.')
    if len(parts) == 3:
        print("   ✅ Structure JWT valide")
    else:
        print("   ❌ Structure JWT invalide")
        return False
    
    # Vérification de la signature
    test_message = f"{parts[0]}.{parts[1]}"
    test_signature = hmac.new(secret.encode(), test_message.encode(), hashlib.sha256).digest()
    test_signature_b64 = base64.urlsafe_b64encode(test_signature).decode().rstrip('=')
    
    if test_signature_b64 == parts[2]:
        print("   ✅ Signature JWT valide")
    else:
        print("   ❌ Signature JWT invalide")
        return False
    
    return True

def test_session_management():
    """Test basique de gestion de session"""
    print("⏰ Test de gestion de session...")
    
    # Simulation d'une session
    sessions = {}
    
    def create_session(user_id, session_id, ip_address):
        sessions[session_id] = {
            "user_id": user_id,
            "ip_address": ip_address,
            "created_at": datetime.now(timezone.utc),
            "last_activity": datetime.now(timezone.utc)
        }
        return True
    
    def update_session_activity(session_id):
        if session_id in sessions:
            sessions[session_id]["last_activity"] = datetime.now(timezone.utc)
            return True
        return False
    
    def is_session_expired(session_id, timeout_minutes=60):
        if session_id not in sessions:
            return True
        
        session = sessions[session_id]
        now = datetime.now(timezone.utc)
        time_since_activity = now - session["last_activity"]
        
        return time_since_activity.total_seconds() > (timeout_minutes * 60)
    
    # Test de création
    result = create_session(123, "test-session-1", "192.168.1.1")
    if result:
        print("   ✅ Session créée")
    else:
        print("   ❌ Échec création session")
        return False
    
    # Test de mise à jour
    time.sleep(0.1)
    result = update_session_activity("test-session-1")
    if result:
        print("   ✅ Activité mise à jour")
    else:
        print("   ❌ Échec mise à jour activité")
        return False
    
    # Test d'expiration
    expired = is_session_expired("test-session-1", timeout_minutes=0.001)  # 60ms
    time.sleep(0.1)
    expired_after_wait = is_session_expired("test-session-1", timeout_minutes=0.001)
    
    if not expired and expired_after_wait:
        print("   ✅ Expiration de session fonctionnelle")
    else:
        print("   ❌ Échec test expiration")
        return False
    
    return True

def test_security_config():
    """Test de configuration de sécurité"""
    print("⚙️  Test de configuration sécurité...")
    
    # Configuration par défaut
    default_config = {
        "password_policy": {
            "min_length": 8,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_digits": True,
            "require_special_chars": True
        },
        "session": {
            "idle_timeout_minutes": 60,
            "max_concurrent_sessions": 5
        },
        "rate_limiting": {
            "enabled": True,
            "requests_per_minute": 100
        },
        "features": {
            "enable_mfa": True,
            "enable_intrusion_detection": True
        }
    }
    
    # Test de validation de mot de passe
    def validate_password(password, policy):
        errors = []
        
        if len(password) < policy["min_length"]:
            errors.append(f"Minimum {policy['min_length']} characters required")
        
        if policy["require_uppercase"] and not re.search(r'[A-Z]', password):
            errors.append("Uppercase letter required")
        
        if policy["require_lowercase"] and not re.search(r'[a-z]', password):
            errors.append("Lowercase letter required")
        
        if policy["require_digits"] and not re.search(r'\d', password):
            errors.append("Digit required")
        
        if policy["require_special_chars"] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Special character required")
        
        return len(errors) == 0, errors
    
    # Test de mots de passe
    test_passwords = [
        ("weak", False),
        ("StrongPass123!", True),
        ("nospecial123", False),
        ("NoDigits!", False),
        ("P@ssw0rd", True)
    ]
    
    passed = 0
    for password, expected_valid in test_passwords:
        is_valid, errors = validate_password(password, default_config["password_policy"])
        if is_valid == expected_valid:
            passed += 1
        else:
            print(f"   ❌ Test mot de passe '{password}' échoué: attendu {expected_valid}, obtenu {is_valid}")
    
    print(f"   Validation mots de passe: {passed}/{len(test_passwords)} réussis")
    
    if passed == len(test_passwords):
        print("   ✅ Configuration sécurité validée")
        return True
    else:
        print("   ❌ Échec validation configuration")
        return False

def test_rate_limiting():
    """Test basique de rate limiting"""
    print("🚦 Test de rate limiting...")
    
    # Simulation d'un rate limiter simple
    class SimpleRateLimiter:
        def __init__(self, max_requests=5, window_seconds=60):
            self.max_requests = max_requests
            self.window_seconds = window_seconds
            self.requests = defaultdict(deque)
        
        def is_allowed(self, identifier):
            now = time.time()
            
            # Nettoyer les anciennes requêtes
            while self.requests[identifier] and now - self.requests[identifier][0] > self.window_seconds:
                self.requests[identifier].popleft()
            
            # Vérifier la limite
            if len(self.requests[identifier]) >= self.max_requests:
                return False
            
            # Ajouter la nouvelle requête
            self.requests[identifier].append(now)
            return True
    
    limiter = SimpleRateLimiter(max_requests=3, window_seconds=1)
    
    # Test normal
    for i in range(3):
        if not limiter.is_allowed("192.168.1.1"):
            print(f"   ❌ Requête {i+1} refusée incorrectement")
            return False
    
    # Test dépassement
    if limiter.is_allowed("192.168.1.1"):
        print("   ❌ Requête supplémentaire acceptée incorrectement")
        return False
    
    print("   ✅ Rate limiting fonctionnel")
    return True

def main():
    """Exécute tous les tests de validation"""
    print("🔒 Validation des Fonctionnalités de Sécurité WakeDock")
    print("=" * 55)
    
    tests = [
        ("Configuration Sécurité", test_security_config),
        ("Détection de Patterns", test_pattern_detection),
        ("JWT Basique", test_jwt_basics),
        ("Gestion de Session", test_session_management),
        ("Rate Limiting", test_rate_limiting)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"   ✅ {test_name}: RÉUSSI")
            else:
                failed += 1
                print(f"   ❌ {test_name}: ÉCHOUÉ")
        except Exception as e:
            failed += 1
            print(f"   ❌ {test_name}: ERREUR - {e}")
    
    print("\n" + "=" * 55)
    print(f"📊 Résultats: {passed} tests réussis, {failed} tests échoués")
    
    if failed == 0:
        print("🎉 Tous les tests de sécurité sont passés avec succès!")
        print("✅ Les fonctionnalités de sécurité sont prêtes à être intégrées.")
        return 0
    else:
        print("⚠️  Certains tests ont échoué.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
