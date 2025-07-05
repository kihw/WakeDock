#!/usr/bin/env python3
"""
Test de validation des services de sécurité
Vérification simple que les modules peuvent être importés et utilisés
"""

import sys
import os

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_jwt_rotation():
    """Test basique du service de rotation JWT"""
    try:
        from wakedock.security.jwt_rotation import JWTRotationService
        
        service = JWTRotationService(
            secret_key="test-secret-key",
            access_token_expire_minutes=30
        )
        
        # Test de création de tokens
        tokens = service.create_token_pair(user_id=123)
        assert tokens.access_token
        assert tokens.refresh_token
        
        # Test de décodage
        payload = service.decode_token(tokens.access_token)
        assert payload is not None
        assert payload["user_id"] == 123
        
        print("✅ Test JWT Rotation: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Test JWT Rotation: FAILED - {e}")
        return False

def test_session_timeout():
    """Test basique du gestionnaire de timeout de session"""
    try:
        from wakedock.security.session_timeout import SessionTimeoutManager
        
        manager = SessionTimeoutManager(
            idle_timeout_minutes=60,
            max_concurrent_sessions=5
        )
        
        # Test de création de session
        result = manager.create_session(
            user_id=123,
            session_id="test-session-1",
            ip_address="192.168.1.1",
            user_agent="Test Agent"
        )
        assert result is True
        
        # Test de mise à jour d'activité
        result = manager.update_session_activity("test-session-1")
        assert result is True
        
        print("✅ Test Session Timeout: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Test Session Timeout: FAILED - {e}")
        return False

def test_intrusion_detection():
    """Test basique du système de détection d'intrusion"""
    try:
        from wakedock.security.intrusion_detection import IntrusionDetectionSystem
        
        ids = IntrusionDetectionSystem()
        
        # Test de détection SQL injection
        events = ids.analyze_request(
            ip_address="192.168.1.1",
            endpoint="/api/users",
            method="GET",
            user_agent="Test Agent",
            payload="id=1' OR '1'='1"
        )
        
        assert len(events) > 0
        
        # Test de blocage d'IP
        ids.block_ip("192.168.1.100")
        assert ids.is_ip_blocked("192.168.1.100")
        
        print("✅ Test Intrusion Detection: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Test Intrusion Detection: FAILED - {e}")
        return False

def test_security_config():
    """Test basique de la configuration de sécurité"""
    try:
        from wakedock.security.config import SecurityConfig, SecurityConfigManager
        
        config = SecurityConfig()
        assert config.environment == "production"
        assert config.session.idle_timeout_minutes == 60
        
        manager = SecurityConfigManager()
        config = manager.get_config()
        assert config is not None
        
        print("✅ Test Security Config: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Test Security Config: FAILED - {e}")
        return False

def main():
    """Exécute tous les tests de validation"""
    print("🔒 Validation des Services de Sécurité WakeDock")
    print("=" * 50)
    
    tests = [
        test_security_config,
        test_jwt_rotation,
        test_session_timeout,
        test_intrusion_detection
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Résultats: {passed} tests réussis, {failed} tests échoués")
    
    if failed == 0:
        print("🎉 Tous les tests de sécurité sont passés avec succès!")
        return 0
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les dépendances.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
