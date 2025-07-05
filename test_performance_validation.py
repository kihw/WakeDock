#!/usr/bin/env python3
"""
Test de validation des optimisations de performance WakeDock
Vérifie que toutes les optimisations sont correctement intégrées
"""

import sys
import os
import asyncio
import time
from datetime import datetime
from pathlib import Path

def test_performance_files_exist():
    """Vérifie que tous les fichiers d'optimisation existent"""
    print("📁 Test de présence des fichiers d'optimisation")
    
    performance_files = [
        "src/wakedock/performance/cache/intelligent.py",
        "src/wakedock/performance/database/optimizer.py",
        "src/wakedock/performance/api/middleware.py",
        "src/wakedock/performance/integration.py",
        "docker-compose.performance.yml",
        "Dockerfile.performance",
        "dashboard/Dockerfile.performance",
        "docker/nginx.performance.conf",
        "scripts/performance_benchmark.py"
    ]
    
    missing_files = []
    for file_path in performance_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"   ❌ Fichiers manquants: {missing_files}")
        return False
    
    print(f"   ✅ Tous les {len(performance_files)} fichiers d'optimisation sont présents")
    return True


def test_main_py_performance_integration():
    """Vérifie que main.py contient les imports de performance"""
    print("🔧 Test de l'intégration performance dans main.py")
    
    main_py_path = "src/wakedock/main.py"
    
    if not os.path.exists(main_py_path):
        print("   ❌ main.py non trouvé")
        return False
    
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    required_imports = [
        "from wakedock.performance.integration import",
        "initialize_performance",
        "shutdown_performance",
        "get_performance_manager"
    ]
    
    missing_imports = []
    for import_stmt in required_imports:
        if import_stmt not in content:
            missing_imports.append(import_stmt)
    
    if missing_imports:
        print(f"   ❌ Imports performance manquants: {missing_imports}")
        return False
    
    # Vérifier les points clés d'intégration
    integration_points = [
        "performance_manager =",
        "await initialize_performance",
        "app.state.performance_manager",
        "await shutdown_performance"
    ]
    
    missing_integration = []
    for point in integration_points:
        if point not in content:
            missing_integration.append(point)
    
    if missing_integration:
        print(f"   ❌ Points d'intégration performance manquants: {missing_integration}")
        return False
    
    print("   ✅ main.py correctement intégré avec les optimisations de performance")
    return True


def test_performance_config_files():
    """Vérifie les fichiers de configuration de performance"""
    print("⚙️  Test des fichiers de configuration performance")
    
    config_files = {
        "docker-compose.performance.yml": [
            "resources:",
            "limits:",
            "reservations:",
            "healthcheck:",
            "logging:"
        ],
        "Dockerfile.performance": [
            "FROM python:3.11-slim as base",
            "COPY --from=dependencies",
            "healthcheck:",
            "useradd"
        ],
        "dashboard/Dockerfile.performance": [
            "FROM node:18-alpine",
            "nginx:alpine",
            "gzip -k",
            "HEALTHCHECK"
        ]
    }
    
    for config_file, required_content in config_files.items():
        if not os.path.exists(config_file):
            print(f"   ❌ {config_file} manquant")
            return False
        
        with open(config_file, 'r') as f:
            content = f.read()
        
        missing_content = []
        for required in required_content:
            if required not in content:
                missing_content.append(required)
        
        if missing_content:
            print(f"   ❌ {config_file} contenu manquant: {missing_content}")
            return False
    
    print("   ✅ Tous les fichiers de configuration performance sont corrects")
    return True


def test_performance_modules_import():
    """Test d'import des modules de performance"""
    print("🐍 Test d'import des modules performance")
    
    try:
        sys.path.insert(0, str(Path("src").resolve()))
        
        # Test imports cache
        from wakedock.performance.cache.intelligent import IntelligentCache, CacheStrategy
        print("   ✅ Module cache intelligent importé")
        
        # Test imports database
        from wakedock.performance.database.optimizer import DatabaseOptimizer
        print("   ✅ Module optimiseur database importé")
        
        # Test imports API middleware  
        from wakedock.performance.api.middleware import PerformanceMiddleware
        print("   ✅ Module middleware API importé")
        
        # Test imports integration
        from wakedock.performance.integration import PerformanceManager, get_performance_manager
        print("   ✅ Module intégration performance importé")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Erreur inattendue: {e}")
        return False


def test_docker_optimization_features():
    """Vérifie les fonctionnalités d'optimisation Docker"""
    print("🐳 Test des optimisations Docker")
    
    # Vérifier docker-compose.performance.yml
    compose_file = "docker-compose.performance.yml"
    if not os.path.exists(compose_file):
        print("   ❌ docker-compose.performance.yml manquant")
        return False
    
    with open(compose_file, 'r') as f:
        content = f.read()
    
    optimizations = [
        "deploy:",
        "resources:",
        "cpus:",
        "memory:",
        "healthcheck:",
        "shared_preload_libraries=pg_stat_statements",  # PostgreSQL optimizations
        "maxmemory 256mb",  # Redis optimizations
        "compress: \"true\""  # Logging optimizations
    ]
    
    missing_optimizations = []
    for opt in optimizations:
        if opt not in content:
            missing_optimizations.append(opt)
    
    if missing_optimizations:
        print(f"   ❌ Optimisations Docker manquantes: {missing_optimizations}")
        return False
    
    print("   ✅ Optimisations Docker correctement configurées")
    return True


def test_nginx_performance_config():
    """Vérifie la configuration nginx optimisée"""
    print("🌐 Test de la configuration nginx performance")
    
    nginx_config = "docker/nginx.performance.conf"
    if not os.path.exists(nginx_config):
        print("   ❌ nginx.performance.conf manquant")
        return False
    
    with open(nginx_config, 'r') as f:
        content = f.read()
    
    performance_features = [
        "gzip on;",
        "gzip_comp_level",
        "expires 1y;",
        "Cache-Control",
        "worker_processes auto;",
        "worker_connections",
        "sendfile on;",
        "tcp_nopush on;",
        "open_file_cache"
    ]
    
    missing_features = []
    for feature in performance_features:
        if feature not in content:
            missing_features.append(feature)
    
    if missing_features:
        print(f"   ❌ Fonctionnalités nginx manquantes: {missing_features}")
        return False
    
    print("   ✅ Configuration nginx performance correcte")
    return True


def test_benchmark_script():
    """Vérifie le script de benchmark"""
    print("📊 Test du script de benchmark")
    
    benchmark_script = "scripts/performance_benchmark.py"
    if not os.path.exists(benchmark_script):
        print("   ❌ Script de benchmark manquant")
        return False
    
    with open(benchmark_script, 'r') as f:
        content = f.read()
    
    benchmark_features = [
        "class PerformanceBenchmark",
        "benchmark_api_endpoints",
        "load_test_endpoint",
        "benchmark_system_resources",
        "run_full_benchmark",
        "async def main():"
    ]
    
    missing_features = []
    for feature in benchmark_features:
        if feature not in content:
            missing_features.append(feature)
    
    if missing_features:
        print(f"   ❌ Fonctionnalités benchmark manquantes: {missing_features}")
        return False
    
    print("   ✅ Script de benchmark complet")
    return True


def test_performance_code_quality():
    """Test basique de qualité du code performance"""
    print("🔍 Test de qualité du code performance")
    
    performance_files = [
        "src/wakedock/performance/cache/intelligent.py",
        "src/wakedock/performance/database/optimizer.py",
        "src/wakedock/performance/api/middleware.py",
        "src/wakedock/performance/integration.py"
    ]
    
    total_lines = 0
    total_files = 0
    
    for file_path in performance_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = len(f.readlines())
                total_lines += lines
                total_files += 1
                print(f"   📄 {os.path.basename(file_path)}: {lines} lignes")
    
    if total_files == 0:
        print("   ❌ Aucun fichier de performance trouvé")
        return False
    
    avg_lines = total_lines / total_files
    print(f"   📊 Moyenne: {avg_lines:.0f} lignes par fichier")
    print(f"   📊 Total: {total_lines} lignes de code performance")
    
    if total_lines < 800:
        print("   ⚠️  Code de performance peut-être incomplet")
        return False
    
    print("   ✅ Volume de code performance approprié")
    return True


def main():
    """Exécute la validation des optimisations de performance"""
    print("\n" + "="*70)
    print("🚀 VALIDATION DES OPTIMISATIONS DE PERFORMANCE WAKEDOCK")
    print("="*70)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        test_performance_files_exist,
        test_main_py_performance_integration,
        test_performance_config_files,
        test_performance_modules_import,
        test_docker_optimization_features,
        test_nginx_performance_config,
        test_benchmark_script,
        test_performance_code_quality
    ]
    
    results = []
    for test_func in tests:
        try:
            start_time = time.time()
            result = test_func()
            end_time = time.time()
            
            results.append(result)
            print(f"   ⏱️  Durée: {(end_time - start_time)*1000:.1f}ms\n")
            
        except Exception as e:
            print(f"   💥 Erreur durant le test: {e}\n")
            results.append(False)
    
    # Résumé
    print("="*70)
    print("📋 RÉSUMÉ DES TESTS DE PERFORMANCE")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"✅ Tests réussis: {passed}/{total} ({success_rate:.1f}%)")
    
    if passed == total:
        print("🎉 TOUTES LES OPTIMISATIONS DE PERFORMANCE SONT CORRECTEMENT INTÉGRÉES!")
        print("\n🚀 Recommandations:")
        print("  - Exécuter les benchmarks de performance")
        print("  - Surveiller les métriques en production")
        print("  - Optimiser selon les résultats des tests de charge")
        return 0
    else:
        print("⚠️  CERTAINES OPTIMISATIONS NÉCESSITENT DE L'ATTENTION")
        print("\n📝 Actions requises:")
        print("  - Corriger les tests en échec")
        print("  - Vérifier l'intégration des modules")
        print("  - Valider la configuration Docker")
        return 1


if __name__ == "__main__":
    sys.exit(main())
