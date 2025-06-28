#!/usr/bin/env python3
"""
Script pour vérifier que tous les imports fonctionnent correctement
"""

import sys
import os
import importlib
from pathlib import Path

# Ajouter le dossier src au PYTHONPATH
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_import(module_name):
    """Test l'import d'un module"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {module_name}: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name}: {e}")
        return False

def main():
    """Test tous les modules principaux"""
    modules_to_test = [
        # Core modules
        "wakedock.config",
        "wakedock.main",
        
        # Database
        "wakedock.database.database",
        "wakedock.database.models",
        
        # API
        "wakedock.api.app",
        "wakedock.api.dependencies",
        "wakedock.api.routes.services",
        "wakedock.api.routes.system",
        "wakedock.api.routes.health",
        
        # Authentication
        "wakedock.api.auth.jwt",
        "wakedock.api.auth.models",
        "wakedock.api.auth.dependencies",
        "wakedock.api.auth.password",
        "wakedock.api.auth.routes",
        
        # Core services
        "wakedock.core.orchestrator",
        "wakedock.core.monitoring",
        "wakedock.core.health",
        "wakedock.core.caddy",
        
        # Security
        "wakedock.security.validation",
        "wakedock.security.rate_limit",
        
        # Utils
        "wakedock.utils.helpers",
        "wakedock.utils.validation",
        
        # Metrics
        "wakedock.metrics",
    ]
    
    print("🔍 Test des imports WakeDock")
    print("=" * 50)
    
    success_count = 0
    total_count = len(modules_to_test)
    
    for module in modules_to_test:
        if test_import(module):
            success_count += 1
    
    print("=" * 50)
    print(f"📊 Résultats: {success_count}/{total_count} modules importés avec succès")
    
    if success_count == total_count:
        print("🎉 Tous les imports fonctionnent correctement!")
        return True
    else:
        print("⚠️  Certains imports ont échoué")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
