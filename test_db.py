#!/usr/bin/env python3
"""Test database initialization."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_database():
    """Test database initialization."""
    print("Testing database initialization...")
    
    # This should not cause errors during import
    try:
        from wakedock.database.database import get_db_manager
        print("✅ Database module imported successfully")
    except Exception as e:
        print(f"❌ Failed to import database module: {e}")
        return False
    
    # Test getting the manager (should not initialize yet)
    try:
        db_manager = get_db_manager()
        print("✅ Database manager created successfully")
    except Exception as e:
        print(f"❌ Failed to create database manager: {e}")
        return False
    
    # Test initialization
    try:
        db_manager.initialize()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)
