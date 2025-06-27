#!/usr/bin/env python3
"""Test database initialization with permission handling."""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_database():
    """Test database initialization with various scenarios."""
    print("Testing database initialization...")
    
    # Test 1: Import without errors
    try:
        from wakedock.database.database import get_db_manager
        print("✅ Database module imported successfully")
    except Exception as e:
        print(f"❌ Failed to import database module: {e}")
        return False
    
    # Test 2: Create manager without initialization
    try:
        db_manager = get_db_manager()
        print("✅ Database manager created successfully")
        print(f"   Initial state: initialized={getattr(db_manager, '_initialized', False)}")
    except Exception as e:
        print(f"❌ Failed to create database manager: {e}")
        return False
    
    # Test 3: Test initialization with writable directory
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set a temporary data path that should be writable
            os.environ['WAKEDOCK_DATA_PATH'] = temp_dir
            
            # Create a new manager to test the fallback
            from wakedock.database.database import DatabaseManager
            test_manager = DatabaseManager()
            test_manager.initialize()
            print("✅ Database initialized in writable directory")
            
            # Test table creation
            test_manager.create_tables()
            print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database in temp directory: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False
    
    # Test 4: Test fallback behavior (simulate permission error)
    try:
        # Set an impossible path to trigger fallback
        os.environ['WAKEDOCK_DATA_PATH'] = '/root/impossible/path'
        
        # Create new manager to test fallback
        fallback_manager = DatabaseManager()
        fallback_manager.initialize()
        print("✅ Database fallback mechanism works")
        
        # Check if it's using /tmp
        if '/tmp' in fallback_manager.database_url:
            print("✅ Correctly using fallback path")
        else:
            print(f"⚠️  Unexpected database URL: {fallback_manager.database_url}")
    except Exception as e:
        print(f"❌ Fallback mechanism failed: {e}")
        return False
    finally:
        # Reset environment
        if 'WAKEDOCK_DATA_PATH' in os.environ:
            del os.environ['WAKEDOCK_DATA_PATH']
    
    return True

if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)
