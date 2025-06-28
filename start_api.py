#!/usr/bin/env python3
"""
Script simple pour démarrer l'API WakeDock
"""

import sys
import os
from pathlib import Path

# Ajouter src au PYTHONPATH
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Variables d'environnement pour les tests
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-development-only")
os.environ.setdefault("WAKEDOCK_DEBUG", "true")
os.environ.setdefault("WAKEDOCK_LOG_LEVEL", "INFO")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

if __name__ == "__main__":
    import uvicorn
    from wakedock.api.app import create_app
    
    print("🚀 Démarrage de WakeDock API...")
    print("🌐 API Docs: http://localhost:8001/api/docs")
    print("🔐 Login: POST http://localhost:8001/api/v1/auth/login")
    
    app = create_app()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
