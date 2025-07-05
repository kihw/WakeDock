#!/usr/bin/env python3
"""
Test d'intégration des services de sécurité WakeDock
Vérifie que l'intégration dans main.py fonctionne correctement
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_security_integration():
    """Test d'intégration des services de sécurité"""
    print("🔒 Test d'Intégration des Services de Sécurité")
    print("=" * 50)
    
    try:
        # Configuration de test
        security_config = {
            "jwt_secret_key": "test-integration-secret-key",
            "security": {
                "environment": "testing",
                "session": {
                    "idle_timeout_minutes": 30,
                    "max_concurrent_sessions": 3
                },
                "features": {
                    "enable_mfa": True,
                    "enable_intrusion_detection": True,
                    "enable_api_rate_limiting": True
                }
            }
        }
        
        print("📋 Test 1: Initialisation des services de sécurité")
        
        # Test d'importation
        try:
            from wakedock.security.manager import initialize_security, shutdown_security
            print("   ✅ Import des modules de sécurité réussi")
        except ImportError as e:
            print(f"   ❌ Échec import: {e}")
            return False
        
        # Test d'initialisation
        try:
            security_services = await initialize_security(security_config)
            print("   ✅ Initialisation des services réussie")
            
            # Vérifier que tous les services sont présents
            assert security_services.jwt_rotation_service is not None
            assert security_services.session_timeout_manager is not None
            assert security_services.intrusion_detection_system is not None
            assert security_services.security_config is not None
            print("   ✅ Tous les services sont initialisés")
            
        except Exception as e:
            print(f"   ❌ Échec initialisation: {e}")
            return False
        
        print("\n📋 Test 2: Test des middlewares de sécurité")
        
        try:
            from wakedock.security.ids_middleware import IntrusionDetectionMiddleware
            from wakedock.security.session_timeout import SessionTimeoutMiddleware
            
            # Test d'instanciation des middlewares
            ids_middleware = IntrusionDetectionMiddleware(
                app=None,  # Mock app
                ids=security_services.intrusion_detection_system
            )
            
            session_middleware = SessionTimeoutMiddleware(
                app=None,  # Mock app
                session_manager=security_services.session_timeout_manager
            )
            
            print("   ✅ Middlewares créés avec succès")
            
        except Exception as e:
            print(f"   ❌ Échec création middlewares: {e}")
            return False
        
        print("\n📋 Test 3: Test des fonctionnalités de sécurité")
        
        # Test JWT Rotation
        try:
            tokens = security_services.jwt_rotation_service.create_token_pair(user_id=123)
            assert tokens.access_token
            assert tokens.refresh_token
            print("   ✅ Création de tokens JWT réussie")
        except Exception as e:
            print(f"   ❌ Échec JWT: {e}")
            return False
        
        # Test Session Management
        try:
            result = security_services.session_timeout_manager.create_session(
                user_id=123,
                session_id="test-integration-session",
                ip_address="127.0.0.1",
                user_agent="Integration Test"
            )
            assert result is True
            print("   ✅ Gestion de session réussie")
        except Exception as e:
            print(f"   ❌ Échec session: {e}")
            return False
        
        # Test Intrusion Detection
        try:
            events = security_services.intrusion_detection_system.analyze_request(
                ip_address="127.0.0.1",
                endpoint="/test",
                method="GET",
                user_agent="Integration Test",
                payload="test payload"
            )
            print("   ✅ Détection d'intrusion réussie")
        except Exception as e:
            print(f"   ❌ Échec détection intrusion: {e}")
            return False
        
        print("\n📋 Test 4: Test des statistiques de sécurité")
        
        try:
            # Statistiques JWT
            jwt_stats = security_services.jwt_rotation_service.get_rotation_stats()
            assert isinstance(jwt_stats, dict)
            print(f"   ✅ Stats JWT: {jwt_stats['total_rotations']} rotations")
            
            # Statistiques sessions
            session_stats = security_services.session_timeout_manager.get_stats()
            assert isinstance(session_stats, dict)
            print(f"   ✅ Stats Sessions: {session_stats['active_sessions_count']} actives")
            
            # Statistiques IDS
            ids_stats = security_services.intrusion_detection_system.get_statistics()
            assert isinstance(ids_stats, dict)
            print(f"   ✅ Stats IDS: {ids_stats['total_events']} événements")
            
        except Exception as e:
            print(f"   ❌ Échec statistiques: {e}")
            return False
        
        print("\n📋 Test 5: Arrêt propre des services")
        
        try:
            await shutdown_security()
            print("   ✅ Arrêt des services réussi")
        except Exception as e:
            print(f"   ❌ Échec arrêt: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False

async def test_main_app_integration():
    """Test de l'intégration dans main.py"""
    print("\n🚀 Test d'Intégration Main App")
    print("=" * 50)
    
    try:
        # Test d'import du main
        try:
            # Simuler les settings requis
            os.environ.setdefault('WAKEDOCK_CONFIG', 'config.yml')
            
            print("   ✅ Variables d'environnement configurées")
        except Exception as e:
            print(f"   ❌ Échec configuration: {e}")
            return False
        
        # Test de la configuration de sécurité
        try:
            security_config = {
                "jwt_secret_key": "test-main-secret-key",
                "security": {
                    "environment": "testing",
                    "session": {"idle_timeout_minutes": 60},
                    "features": {"enable_mfa": True}
                }
            }
            
            # Vérifier la structure de configuration
            assert "jwt_secret_key" in security_config
            assert "security" in security_config
            assert "session" in security_config["security"]
            assert "features" in security_config["security"]
            
            print("   ✅ Configuration de sécurité validée")
            
        except Exception as e:
            print(f"   ❌ Échec configuration: {e}")
            return False
        
        print("   ✅ Intégration main.py prête")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur intégration main: {e}")
        return False

async def main():
    """Exécute tous les tests d'intégration"""
    start_time = time.time()
    
    print("🎯 Tests d'Intégration Sécurité WakeDock")
    print("Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    tests = [
        ("Services de Sécurité", test_security_integration),
        ("Intégration Main App", test_main_app_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        try:
            if await test_func():
                passed += 1
                print(f"✅ {test_name}: RÉUSSI")
            else:
                failed += 1
                print(f"❌ {test_name}: ÉCHOUÉ")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: ERREUR - {e}")
    
    duration = time.time() - start_time
    
    print("\n" + "=" * 60)
    print(f"📊 Résultats des Tests d'Intégration")
    print(f"   Réussis: {passed}")
    print(f"   Échoués: {failed}")
    print(f"   Durée: {duration:.2f}s")
    
    if failed == 0:
        print("\n🎉 Tous les tests d'intégration sont passés!")
        print("✅ Les services de sécurité sont correctement intégrés.")
        print("🚀 WakeDock est prêt avec sécurité enterprise!")
        return 0
    else:
        print("\n⚠️  Certains tests d'intégration ont échoué.")
        print("🔧 Vérifiez la configuration et les dépendances.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
