#!/usr/bin/env python3
"""
Simple test script to verify configuration loading
"""
import sys
import os

# Add src to path
sys.path.insert(0, '/app/src')

try:
    print("Testing configuration loading...")
    from wakedock.config import get_settings
    
    settings = get_settings()
    print("✅ Settings loaded successfully")
    print(f"WakeDock domain: {settings.wakedock.domain}")
    print(f"WakeDock data_path: {settings.wakedock.data_path}")
    print(f"Database URL: {settings.database.url}")
    print(f"Caddy API endpoint: {settings.caddy.api_endpoint}")
    
    print("\nTesting database initialization...")
    from wakedock.database.database import DatabaseManager
    db_manager = DatabaseManager()
    print("✅ Database manager created successfully")
    print(f"Database URL: {db_manager.database_url}")
    
    print("\n✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
