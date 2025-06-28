#!/usr/bin/env python3
"""
Simple test script to validate WakeDock functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all critical modules can be imported"""
    try:
        from wakedock.config import get_settings
        print("✓ Config module imported successfully")
        
        from wakedock.database.models import User, Service, Configuration
        print("✓ Database models imported successfully")
        
        from wakedock.api.dependencies import get_orchestrator, get_monitoring_service
        print("✓ API dependencies imported successfully")
        
        from wakedock.core.monitoring import MonitoringService
        print("✓ Monitoring service imported successfully")
        
        from wakedock.core.orchestrator import DockerOrchestrator
        print("✓ Docker orchestrator imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    try:
        from wakedock.config import get_settings
        settings = get_settings()
        print(f"✓ Configuration loaded successfully")
        print(f"  - Host: {settings.wakedock.host}")
        print(f"  - Port: {settings.wakedock.port}")
        print(f"  - Data path: {settings.wakedock.data_path}")
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_database_connection():
    """Test database initialization"""
    try:
        from wakedock.database.database import get_db_manager
        db_manager = get_db_manager()
        db_manager.initialize()
        print("✓ Database initialization successful")
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_monitoring_service():
    """Test monitoring service initialization"""
    try:
        from wakedock.core.monitoring import MonitoringService
        monitoring = MonitoringService()
        print("✓ Monitoring service created successfully")
        return True
    except Exception as e:
        print(f"✗ Monitoring service test failed: {e}")
        return False

def test_orchestrator():
    """Test orchestrator initialization"""
    try:
        from wakedock.core.orchestrator import DockerOrchestrator
        # Don't actually connect to Docker in tests
        print("✓ Docker orchestrator module imported successfully")
        return True
    except Exception as e:
        print(f"✗ Orchestrator test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("WakeDock Component Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_database_connection,
        test_monitoring_service,
        test_orchestrator,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\n[TEST] {test.__name__}")
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
