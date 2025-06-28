#!/usr/bin/env python3
"""
Script de test rapide pour WakeDock
Lance l'API backend sans Docker pour tester l'authentification
"""

import asyncio
import os
import sys
import uvicorn
from pathlib import Path

# Ajouter le dossier src au PYTHONPATH
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Variables d'environnement pour les tests
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-development-only")
os.environ.setdefault("WAKEDOCK_DEBUG", "true")
os.environ.setdefault("WAKEDOCK_LOG_LEVEL", "INFO")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

async def main():
    """Lancer l'API WakeDock en mode test"""
    print("🚀 Démarrage de WakeDock API en mode test...")
    print("=" * 50)
    
    try:
        # Import des modules WakeDock
        from wakedock.main import main as wakedock_main
        
        print("✅ Modules WakeDock importés avec succès")
        
        # Créer l'application FastAPI directement
        from wakedock.api.app import create_app
        app = create_app()
        print("✅ Application FastAPI créée")
        
        # Créer un utilisateur par défaut pour les tests
        from wakedock.database.database import get_db_session
        from wakedock.database.models import User, UserRole
        from wakedock.api.auth.password import hash_password
        
        try:
            # Créer la session de base de données
            db = next(get_db_session())
            
            # Vérifier si l'utilisateur admin existe
            admin_user = db.query(User).filter(User.username == "admin").first()
            if not admin_user:
                admin_user = User(
                    username="admin",
                    email="admin@wakedock.local",
                    hashed_password=hash_password("admin123"),
                    full_name="Administrator",
                    role=UserRole.ADMIN,
                    is_active=True
                )
                db.add(admin_user)
                db.commit()
                print("✅ Utilisateur admin créé (admin/admin123)")
            else:
                print("✅ Utilisateur admin existe déjà")
            
            db.close()
        except Exception as e:
            print(f"⚠️ Erreur base de données (normal en mode test): {e}")
            print("✅ Continuons sans base de données persistante")
        
        print("\n🌐 API disponible sur:")
        print("   - API Docs: http://localhost:8000/api/docs")
        print("   - Login:    POST http://localhost:8000/api/v1/auth/login")
        print("   - Register: POST http://localhost:8000/api/v1/auth/register")
        print("\n👤 Compte de test:")
        print("   - Username: admin")
        print("   - Password: admin123")
        print("\n⏹️  Arrêter avec Ctrl+C")
        print("=" * 50)
        
        # Lancer le serveur uvicorn avec l'app directement
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur...")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
