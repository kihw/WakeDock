#!/usr/bin/env python3
"""Test WakeDock startup components individually."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all core modules can be imported."""
    print("Testing imports...")
    
    try:
        from wakedock.config import get_settings
        print("✅ Config module imported")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from wakedock.database.database import get_db_manager
        print("✅ Database module imported")
    except Exception as e:
        print(f"❌ Database import failed: {e}")
        return False
    
    try:
        from wakedock.api.app import create_app
        print("✅ API app module imported")
    except Exception as e:
        print(f"❌ API app import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database initialization."""
    print("\nTesting database...")
    
    try:
        from wakedock.database.database import get_db_manager
        db_manager = get_db_manager()
        print("✅ Database manager created")
        
        # Test initialization
        db_manager.initialize()
        print("✅ Database initialized")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_docker_orchestrator():
    """Test Docker orchestrator initialization."""
    print("\nTesting Docker orchestrator...")
    
    try:
        from wakedock.core.orchestrator import DockerOrchestrator
        orchestrator = DockerOrchestrator()
        
        if orchestrator.client is None:
            print("⚠️ Docker client not available (expected in this environment)")
        else:
            print("✅ Docker client available")
        
        return True
    except Exception as e:
        print(f"❌ Docker orchestrator test failed: {e}")
        return False

def test_api_creation():
    """Test FastAPI app creation."""
    print("\nTesting API app creation...")
    
    try:
        from wakedock.api.app import create_app
        app = create_app()
        print("✅ FastAPI app created successfully")
        return True
    except Exception as e:
        print(f"❌ API app creation failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🐳 WakeDock Component Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_database,
        test_docker_orchestrator,
        test_api_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! WakeDock should start successfully.")
        return 0
    else:
        print("❌ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
