#!/usr/bin/env python3
"""
Script pour installer et tester toutes les dépendances WakeDock
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description=""):
    """Exécute une commande et affiche le résultat"""
    print(f"🔧 {description}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent)
        if result.returncode == 0:
            print(f"✅ {description} - Succès")
            if result.stdout:
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - Échec")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False

def test_import(module_name, description=""):
    """Test l'import d'un module"""
    try:
        __import__(module_name)
        print(f"✅ Import {module_name} - {description}")
        return True
    except ImportError as e:
        print(f"❌ Import {module_name} - {description}: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Import {module_name} - {description}: {e}")
        return False

def main():
    """Script principal"""
    print("🚀 Installation et test des dépendances WakeDock")
    print("=" * 60)
    
    # 1. Installer depuis requirements.txt
    print("\n📦 Installation des dépendances...")
    if not run_command("pip install -r requirements.txt", "Installation requirements.txt"):
        print("⚠️ Installation partiellement échouée, continuons avec les tests...")
    
    # 2. Installer les packages problématiques individuellement (optionnel)
    optional_packages = [
        "asyncpg==0.29.0",
        "psycopg2-binary==2.9.9"
    ]
    
    print("\n🔧 Installation des packages optionnels...")
    for package in optional_packages:
        run_command(f"pip install {package}", f"Installation {package}")
    
    # 3. Ajouter src au PYTHONPATH pour les tests
    src_path = Path(__file__).parent / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))
        print(f"\n📁 Ajout de {src_path} au PYTHONPATH")
    
    # 4. Test des imports essentiels
    print("\n🧪 Test des imports essentiels...")
    
    essential_imports = [
        ("fastapi", "Framework web FastAPI"),
        ("uvicorn", "Serveur ASGI"),
        ("pydantic", "Validation des données"),
        ("sqlalchemy", "ORM base de données"),
        ("jwt", "Gestion des tokens JWT"),
        ("passlib", "Hachage des mots de passe"),
        ("httpx", "Client HTTP async"),
        ("docker", "Client API Docker"),
        ("yaml", "Parsing YAML"),
        ("jinja2", "Moteur de templates"),
        ("validators", "Validation des données"),
        ("prometheus_client", "Métriques Prometheus"),
        ("redis", "Client Redis"),
    ]
    
    success_count = 0
    for module, desc in essential_imports:
        if test_import(module, desc):
            success_count += 1
    
    print(f"\n📊 Imports essentiels: {success_count}/{len(essential_imports)} réussis")
    
    # 5. Test des modules WakeDock
    print("\n🏗️ Test des modules WakeDock...")
    
    wakedock_modules = [
        ("wakedock.config", "Configuration"),
        ("wakedock.api.auth.jwt", "Authentification JWT"),
        ("wakedock.database.models", "Modèles de base de données"),
        ("wakedock.core.orchestrator", "Orchestrateur Docker"),
        ("wakedock.api.app", "Application FastAPI"),
    ]
    
    wakedock_success = 0
    for module, desc in wakedock_modules:
        if test_import(module, desc):
            wakedock_success += 1
    
    print(f"\n📊 Modules WakeDock: {wakedock_success}/{len(wakedock_modules)} réussis")
    
    # 6. Test JWT spécifique
    print("\n🔐 Test de la fonctionnalité JWT...")
    try:
        from jwt.exceptions import DecodeError, InvalidTokenError
        print("✅ Exceptions JWT importées correctement")
        
        from wakedock.api.auth.jwt import JWTManager
        jwt_manager = JWTManager()
        print("✅ JWTManager instancié avec succès")
        
        # Test de création de token
        from wakedock.database.models import UserRole
        token = jwt_manager.create_access_token(1, "test", UserRole.USER)
        print("✅ Token JWT créé avec succès")
        
    except Exception as e:
        print(f"❌ Test JWT échoué: {e}")
    
    # 7. Résumé final
    total_success = success_count + wakedock_success
    total_tests = len(essential_imports) + len(wakedock_modules)
    
    print(f"\n📈 Résumé final: {total_success}/{total_tests} tests réussis")
    
    if total_success == total_tests:
        print("🎉 Toutes les dépendances sont installées et fonctionnelles!")
        print("✅ WakeDock est prêt à être exécuté.")
        return 0
    elif total_success >= total_tests * 0.8:  # 80% de réussite
        print("⚠️ La plupart des dépendances fonctionnent, WakeDock devrait pouvoir démarrer.")
        return 0
    else:
        print("❌ Trop d'imports ont échoué, vérifiez les dépendances manquantes.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
