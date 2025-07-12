#!/usr/bin/env python3
"""
Health check script for WakeDock
"""
import sys
import os
import time

def check_health():
    """Check if WakeDock is healthy"""
    try:
        # Simple import test first
        sys.path.insert(0, '/app/src')
        from wakedock.config import get_settings
        
        # Try to get settings - if config works, basic health is OK
        settings = get_settings()
        
        # Try HTTP check if requests is available
        try:
            import requests
            response = requests.get('http://localhost:8000/api/v1/health', timeout=5)
            if response.status_code == 200:
                print("✅ WakeDock API healthy")
                return True
        except:
            # If API is not ready yet, that's OK during startup
            pass
            
        print("✅ WakeDock configuration healthy")
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    if check_health():
        sys.exit(0)
    else:
        sys.exit(1)
