#!/usr/bin/env python3
"""
Test des endpoints d'authentification WakeDock
"""

import asyncio
import httpx
import json

API_BASE = "http://localhost:8001/api/v1"

async def test_auth_endpoints():
    """Test des endpoints d'authentification"""
    print("🧪 Test des endpoints d'authentification WakeDock")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Health check
        print("1️⃣ Test de l'API Health...")
        try:
            response = await client.get(f"{API_BASE}/health")
            if response.status_code == 200:
                print("✅ API Health: OK")
            else:
                print(f"❌ API Health: {response.status_code}")
        except Exception as e:
            print(f"❌ API Health: Erreur de connexion - {e}")
            return
        
        # Test 2: Register un nouvel utilisateur
        print("\n2️⃣ Test de l'inscription...")
        register_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Password123",
            "full_name": "Test User",
            "role": "user",
            "is_active": True
        }
        
        try:
            response = await client.post(
                f"{API_BASE}/auth/register",
                json=register_data
            )
            if response.status_code == 201:
                print("✅ Inscription: Utilisateur créé avec succès")
                user_data = response.json()
                print(f"   Username: {user_data.get('username')}")
                print(f"   Email: {user_data.get('email')}")
            else:
                print(f"❌ Inscription: {response.status_code}")
                print(f"   Erreur: {response.text}")
        except Exception as e:
            print(f"❌ Inscription: Erreur - {e}")
        
        # Test 3: Login avec l'utilisateur créé
        print("\n3️⃣ Test de la connexion...")
        login_data = {
            "username": "testuser",
            "password": "Password123"
        }
        
        try:
            response = await client.post(
                f"{API_BASE}/auth/login",
                data=login_data,  # OAuth2PasswordRequestForm attend des données form
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                print("✅ Connexion: Login réussi")
                token_data = response.json()
                print(f"   Token type: {token_data.get('token_type')}")
                print(f"   Expires in: {token_data.get('expires_in')} secondes")
                
                # Test d'un endpoint protégé avec le token
                token = token_data.get('access_token')
                if token:
                    print("\n4️⃣ Test d'un endpoint protégé...")
                    headers = {"Authorization": f"Bearer {token}"}
                    response = await client.get(f"{API_BASE}/auth/me", headers=headers)
                    if response.status_code == 200:
                        print("✅ Endpoint protégé: Accès autorisé")
                        user_info = response.json()
                        print(f"   User ID: {user_info.get('id')}")
                        print(f"   Username: {user_info.get('username')}")
                    else:
                        print(f"❌ Endpoint protégé: {response.status_code}")
                
            else:
                print(f"❌ Connexion: {response.status_code}")
                print(f"   Erreur: {response.text}")
        except Exception as e:
            print(f"❌ Connexion: Erreur - {e}")
        
        # Test 4: Test avec de mauvaises credentials
        print("\n5️⃣ Test avec de mauvaises credentials...")
        bad_login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        try:
            response = await client.post(
                f"{API_BASE}/auth/login",
                data=bad_login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 401:
                print("✅ Mauvaises credentials: Correctement rejetées")
            else:
                print(f"❌ Mauvaises credentials: {response.status_code} (attendu 401)")
        except Exception as e:
            print(f"❌ Test mauvaises credentials: Erreur - {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Tests terminés!")
    print("\n💡 Prochaines étapes:")
    print("   1. Démarrer le frontend dashboard")
    print("   2. Tester la connexion via l'interface web")
    print("   3. Vérifier la redirection après login")

if __name__ == "__main__":
    asyncio.run(test_auth_endpoints())
