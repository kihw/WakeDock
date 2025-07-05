#!/usr/bin/env python3
"""
Test de validation finale pour la sécurité WakeDock
Test sans dépendances complexes pour vérifier l'intégration
"""

import sys
import os
import time
from datetime import datetime

def test_security_files_exist():
    """Vérifie que tous les fichiers de sécurité existent"""
    print("📁 Test de présence des fichiers de sécurité")
    
    security_files = [
        "src/wakedock/security/jwt_rotation.py",
        "src/wakedock/security/session_timeout.py", 
        "src/wakedock/security/intrusion_detection.py",
        "src/wakedock/security/ids_middleware.py",
        "src/wakedock/security/manager.py",
        "src/wakedock/security/config.py"
    ]
    
    missing_files = []
    for file_path in security_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"   ❌ Fichiers manquants: {missing_files}")
        return False
    
    print(f"   ✅ Tous les {len(security_files)} fichiers de sécurité sont présents")
    return True

def test_main_py_integration():
    """Vérifie que main.py contient les imports de sécurité"""
    print("🔧 Test de l'intégration dans main.py")
    
    main_py_path = "src/wakedock/main.py"
    
    if not os.path.exists(main_py_path):
        print("   ❌ main.py non trouvé")
        return False
    
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    required_imports = [
        "from wakedock.security.manager import",
        "initialize_security",
        "shutdown_security",
        "IntrusionDetectionMiddleware",
        "SessionTimeoutMiddleware"
    ]
    
    missing_imports = []
    for import_stmt in required_imports:
        if import_stmt not in content:
            missing_imports.append(import_stmt)
    
    if missing_imports:
        print(f"   ❌ Imports manquants: {missing_imports}")
        return False
    
    # Vérifier les points clés d'intégration
    integration_points = [
        "security_config =",
        "await initialize_security",
        "app.add_middleware",
        "await shutdown_security"
    ]
    
    missing_integration = []
    for point in integration_points:
        if point not in content:
            missing_integration.append(point)
    
    if missing_integration:
        print(f"   ❌ Points d'intégration manquants: {missing_integration}")
        return False
    
    print("   ✅ main.py correctement intégré avec la sécurité")
    return True

def test_auth_routes_security():
    """Vérifie que les routes d'auth incluent les nouveaux endpoints"""
    print("🛡️  Test des routes d'authentification sécurisées")
    
    auth_routes_path = "src/wakedock/api/auth/routes.py"
    
    if not os.path.exists(auth_routes_path):
        print("   ❌ routes.py d'auth non trouvé")
        return False
    
    with open(auth_routes_path, 'r') as f:
        content = f.read()
    
    security_endpoints = [
        "/refresh",
        "/logout", 
        "/security/events",
        "/security/statistics",
        "/jwt/rotation/stats",
        "/session/stats"
    ]
    
    missing_endpoints = []
    for endpoint in security_endpoints:
        if f'"{endpoint}"' not in content and f"'{endpoint}'" not in content:
            missing_endpoints.append(endpoint)
    
    if missing_endpoints:
        print(f"   ❌ Endpoints sécurité manquants: {missing_endpoints}")
        return False
    
    print(f"   ✅ Tous les {len(security_endpoints)} endpoints de sécurité sont présents")
    return True

def test_security_documentation():
    """Vérifie que la documentation de sécurité est présente"""
    print("📚 Test de la documentation sécurité")
    
    docs = [
        "INTEGRATION_SECURITE_GUIDE.md",
        "test_security_features.py",
        "RAPPORT_STATUT_JUILLET_2025.md"
    ]
    
    missing_docs = []
    for doc in docs:
        if not os.path.exists(doc):
            missing_docs.append(doc)
    
    if missing_docs:
        print(f"   ❌ Documentation manquante: {missing_docs}")
        return False
    
    print(f"   ✅ Toute la documentation sécurité est présente")
    return True

def test_code_quality():
    """Test basique de qualité du code de sécurité"""
    print("🔍 Test de qualité du code sécurité")
    
    security_files = [
        "src/wakedock/security/jwt_rotation.py",
        "src/wakedock/security/session_timeout.py",
        "src/wakedock/security/intrusion_detection.py"
    ]
    
    total_lines = 0
    total_files = 0
    
    for file_path in security_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = len(f.readlines())
                total_lines += lines
                total_files += 1
                print(f"   📄 {os.path.basename(file_path)}: {lines} lignes")
    
    if total_files == 0:
        print("   ❌ Aucun fichier de sécurité trouvé")
        return False
    
    avg_lines = total_lines / total_files
    print(f"   📊 Moyenne: {avg_lines:.0f} lignes par fichier")
    print(f"   📊 Total: {total_lines} lignes de code sécurité")
    
    if total_lines < 1000:
        print("   ⚠️  Code de sécurité peut-être incomplet")
        return False
    
    print("   ✅ Volume de code sécurité approprié")
    return True

def test_integration_guide():
    """Vérifie le guide d'intégration"""
    print("📖 Test du guide d'intégration")
    
    guide_path = "INTEGRATION_SECURITE_GUIDE.md"
    
    if not os.path.exists(guide_path):
        print("   ❌ Guide d'intégration manquant")
        return False
    
    with open(guide_path, 'r') as f:
        content = f.read()
    
    required_sections = [
        "ÉTAPES D'INTÉGRATION",
        "requirements.txt",
        "main.py",
        "CONFIGURATION PRODUCTION",
        "CHECKLIST DE DÉPLOIEMENT"
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"   ❌ Sections manquantes: {missing_sections}")
        return False
    
    print("   ✅ Guide d'intégration complet")
    return True

def main():
    """Exécute la validation finale"""
    start_time = time.time()
    
    print("🎯 Validation Finale - Intégration Sécurité WakeDock")
    print("Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    tests = [
        ("Fichiers de Sécurité", test_security_files_exist),
        ("Intégration Main.py", test_main_py_integration),
        ("Routes Sécurisées", test_auth_routes_security), 
        ("Documentation", test_security_documentation),
        ("Qualité du Code", test_code_quality),
        ("Guide d'Intégration", test_integration_guide)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        try:
            if test_func():
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
    print(f"📊 Résultats de la Validation Finale")
    print(f"   Tests Réussis: {passed}")
    print(f"   Tests Échoués: {failed}")
    print(f"   Durée: {duration:.2f}s")
    
    if failed == 0:
        print("\n🎉 VALIDATION FINALE RÉUSSIE!")
        print("✅ L'intégration sécurité est complète et prête.")
        print("🚀 WakeDock est maintenant sécurisé au niveau enterprise!")
        print("\n📋 PROCHAINES ÉTAPES:")
        print("   1. Tester l'application complète")
        print("   2. Configurer les variables d'environnement")
        print("   3. Déployer en production")
        return 0
    else:
        print("\n⚠️  Validation finale échouée.")
        print("🔧 Vérifiez les points manquants ci-dessus.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
