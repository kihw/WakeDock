"""
Client HashiCorp Vault pour WakeDock.

Fournit une interface complète pour interagir avec Vault API,
incluant l'authentification, la gestion des secrets et le monitoring.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Callable
import aiohttp
import jwt
from cryptography.fernet import Fernet

from .config import VaultConfig, VaultAuthMethod, VaultSettings

logger = logging.getLogger(__name__)


class VaultAuthenticationError(Exception):
    """Erreur d'authentification Vault"""
    pass


class VaultConnectionError(Exception):
    """Erreur de connexion Vault"""
    pass


class VaultPermissionError(Exception):
    """Erreur de permissions Vault"""
    pass


class VaultClient:
    """Client principal pour l'interaction avec HashiCorp Vault"""
    
    def __init__(self, config: VaultConfig):
        self.config = config
        self.settings = config.settings
        self._session: Optional[aiohttp.ClientSession] = None
        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._auth_lock = asyncio.Lock()
        self._metrics = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "auth_renewals": 0,
            "last_auth_time": None,
            "avg_response_time": 0.0
        }
        
        # Encryption key pour le cache des secrets
        if self.settings.encrypt_cache:
            self._encryption_key = Fernet.generate_key()
            self._cipher = Fernet(self._encryption_key)
        else:
            self._cipher = None
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
    
    async def initialize(self):
        """Initialiser le client Vault"""
        try:
            # Créer session HTTP
            connector = aiohttp.TCPConnector(
                verify_ssl=self.settings.verify_ssl,
                limit=20,
                keepalive_timeout=30
            )
            
            timeout = aiohttp.ClientTimeout(total=self.settings.timeout)
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "WakeDock-Vault-Client/1.0"
                }
            )
            
            # Authentification
            await self._authenticate()
            
            logger.info(f"Vault client initialized successfully (method: {self.settings.auth_method.value})")
            
        except Exception as e:
            logger.error(f"Failed to initialize Vault client: {e}")
            await self.close()
            raise VaultConnectionError(f"Vault initialization failed: {e}")
    
    async def close(self):
        """Fermer le client Vault"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        
        logger.info("Vault client closed")
    
    async def _authenticate(self):
        """Authentification auprès de Vault"""
        async with self._auth_lock:
            auth_config = self.config.get_auth_config()
            method = auth_config["method"]
            
            start_time = time.time()
            
            try:
                if method == "token":
                    await self._auth_token(auth_config)
                elif method == "approle":
                    await self._auth_approle(auth_config)
                elif method == "kubernetes":
                    await self._auth_kubernetes(auth_config)
                elif method == "userpass":
                    await self._auth_userpass(auth_config)
                elif method == "aws":
                    await self._auth_aws(auth_config)
                elif method == "azure":
                    await self._auth_azure(auth_config)
                elif method == "gcp":
                    await self._auth_gcp(auth_config)
                else:
                    raise VaultAuthenticationError(f"Unsupported auth method: {method}")
                
                self._metrics["auth_renewals"] += 1
                self._metrics["last_auth_time"] = datetime.now()
                
                auth_time = time.time() - start_time
                logger.info(f"Vault authentication successful ({auth_time:.2f}s)")
                
            except Exception as e:
                logger.error(f"Vault authentication failed: {e}")
                raise VaultAuthenticationError(f"Authentication failed: {e}")
    
    async def _auth_token(self, config: Dict[str, Any]):
        """Authentification par token"""
        token = config.get("token")
        if not token:
            raise VaultAuthenticationError("No token provided")
        
        self._token = token
        
        # Vérifier la validité du token
        token_info = await self._request("GET", "/v1/auth/token/lookup-self")
        if token_info:
            expire_time = token_info.get("data", {}).get("expire_time")
            if expire_time:
                self._token_expires_at = datetime.fromisoformat(expire_time.replace("Z", "+00:00"))
    
    async def _auth_approle(self, config: Dict[str, Any]):
        """Authentification AppRole"""
        role_id = config.get("role_id")
        secret_id = config.get("secret_id")
        mount_point = config.get("mount_point", "approle")
        
        if not role_id or not secret_id:
            raise VaultAuthenticationError("AppRole requires role_id and secret_id")
        
        payload = {
            "role_id": role_id,
            "secret_id": secret_id
        }
        
        response = await self._request("POST", f"/v1/auth/{mount_point}/login", data=payload)
        auth_data = response.get("auth", {})
        
        self._token = auth_data.get("client_token")
        if not self._token:
            raise VaultAuthenticationError("No token received from AppRole auth")
        
        # Calculer expiration
        lease_duration = auth_data.get("lease_duration", 3600)
        self._token_expires_at = datetime.now() + timedelta(seconds=lease_duration)
    
    async def _auth_kubernetes(self, config: Dict[str, Any]):
        """Authentification Kubernetes"""
        role = config.get("role")
        jwt_path = config.get("jwt_path")
        mount_point = config.get("mount_point", "kubernetes")
        
        if not role:
            raise VaultAuthenticationError("Kubernetes auth requires role")
        
        # Lire le JWT token
        try:
            with open(jwt_path, 'r') as f:
                jwt_token = f.read().strip()
        except Exception as e:
            raise VaultAuthenticationError(f"Failed to read JWT token from {jwt_path}: {e}")
        
        payload = {
            "role": role,
            "jwt": jwt_token
        }
        
        response = await self._request("POST", f"/v1/auth/{mount_point}/login", data=payload)
        auth_data = response.get("auth", {})
        
        self._token = auth_data.get("client_token")
        if not self._token:
            raise VaultAuthenticationError("No token received from Kubernetes auth")
        
        # Calculer expiration
        lease_duration = auth_data.get("lease_duration", 3600)
        self._token_expires_at = datetime.now() + timedelta(seconds=lease_duration)
    
    async def _auth_userpass(self, config: Dict[str, Any]):
        """Authentification Username/Password"""
        username = config.get("username")
        password = config.get("password")
        mount_point = config.get("mount_point", "userpass")
        
        if not username or not password:
            raise VaultAuthenticationError("Userpass auth requires username and password")
        
        payload = {"password": password}
        
        response = await self._request("POST", f"/v1/auth/{mount_point}/login/{username}", data=payload)
        auth_data = response.get("auth", {})
        
        self._token = auth_data.get("client_token")
        if not self._token:
            raise VaultAuthenticationError("No token received from Userpass auth")
        
        # Calculer expiration
        lease_duration = auth_data.get("lease_duration", 3600)
        self._token_expires_at = datetime.now() + timedelta(seconds=lease_duration)
    
    async def _auth_aws(self, config: Dict[str, Any]):
        """Authentification AWS IAM"""
        role = config.get("role")
        mount_point = config.get("mount_point", "aws")
        
        # Implementation AWS IAM auth (simplifié pour l'exemple)
        # En production, il faudrait utiliser les credentials AWS pour signer la requête
        payload = {
            "role": role,
            "iam_http_request_method": "POST",
            "iam_request_url": f"{self.settings.url}/v1/auth/{mount_point}/login",
            "iam_request_headers": {}
        }
        
        response = await self._request("POST", f"/v1/auth/{mount_point}/login", data=payload)
        auth_data = response.get("auth", {})
        
        self._token = auth_data.get("client_token")
        if not self._token:
            raise VaultAuthenticationError("No token received from AWS auth")
        
        lease_duration = auth_data.get("lease_duration", 3600)
        self._token_expires_at = datetime.now() + timedelta(seconds=lease_duration)
    
    async def _auth_azure(self, config: Dict[str, Any]):
        """Authentification Azure"""
        role = config.get("role")
        mount_point = config.get("mount_point", "azure")
        
        # Implementation Azure auth (simplifié)
        payload = {"role": role}
        
        response = await self._request("POST", f"/v1/auth/{mount_point}/login", data=payload)
        auth_data = response.get("auth", {})
        
        self._token = auth_data.get("client_token")
        if not self._token:
            raise VaultAuthenticationError("No token received from Azure auth")
        
        lease_duration = auth_data.get("lease_duration", 3600)
        self._token_expires_at = datetime.now() + timedelta(seconds=lease_duration)
    
    async def _auth_gcp(self, config: Dict[str, Any]):
        """Authentification Google Cloud Platform"""
        role = config.get("role")
        mount_point = config.get("mount_point", "gcp")
        
        # Implementation GCP auth (simplifié)
        payload = {"role": role}
        
        response = await self._request("POST", f"/v1/auth/{mount_point}/login", data=payload)
        auth_data = response.get("auth", {})
        
        self._token = auth_data.get("client_token")
        if not self._token:
            raise VaultAuthenticationError("No token received from GCP auth")
        
        lease_duration = auth_data.get("lease_duration", 3600)
        self._token_expires_at = datetime.now() + timedelta(seconds=lease_duration)
    
    async def _ensure_authenticated(self):
        """S'assurer que l'authentification est valide"""
        if not self._token:
            await self._authenticate()
            return
        
        # Vérifier si le token expire bientôt
        if self._token_expires_at:
            buffer = timedelta(seconds=self.settings.token_renewal_buffer)
            if datetime.now() + buffer >= self._token_expires_at:
                logger.info("Token expires soon, renewing...")
                await self._authenticate()
    
    async def _request(
        self, 
        method: str, 
        path: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Exécuter une requête HTTP vers Vault"""
        if not self._session:
            raise VaultConnectionError("Client not initialized")
        
        url = f"{self.settings.url}{path}"
        request_headers = {}
        
        # Ajouter token d'authentification (sauf pour auth)
        if self._token and not path.startswith("/v1/auth/"):
            request_headers["X-Vault-Token"] = self._token
        
        # Ajouter namespace si configuré
        if self.settings.namespace:
            request_headers["X-Vault-Namespace"] = self.settings.namespace
        
        # Ajouter headers personnalisés
        if headers:
            request_headers.update(headers)
        
        start_time = time.time()
        
        for attempt in range(self.settings.max_retries + 1):
            try:
                self._metrics["requests_total"] += 1
                
                async with self._session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=request_headers
                ) as response:
                    
                    # Mesurer temps de réponse
                    response_time = time.time() - start_time
                    self._update_avg_response_time(response_time)
                    
                    # Traiter la réponse
                    if response.status == 200:
                        self._metrics["requests_success"] += 1
                        if response.content_type == "application/json":
                            return await response.json()
                        else:
                            return {"data": await response.text()}
                    
                    elif response.status == 204:
                        # No content (normal pour certaines opérations)
                        self._metrics["requests_success"] += 1
                        return {}
                    
                    elif response.status == 403:
                        self._metrics["requests_failed"] += 1
                        error_data = await response.json() if response.content_type == "application/json" else {}
                        raise VaultPermissionError(f"Permission denied: {error_data.get('errors', [])}")
                    
                    elif response.status == 404:
                        # Not found (peut être normal)
                        self._metrics["requests_success"] += 1
                        return None
                    
                    else:
                        error_text = await response.text()
                        if attempt < self.settings.max_retries:
                            logger.warning(f"Vault request failed (attempt {attempt + 1}): {response.status} - {error_text}")
                            await asyncio.sleep(self.settings.retry_delay * (2 ** attempt))
                            continue
                        else:
                            self._metrics["requests_failed"] += 1
                            raise VaultConnectionError(f"Request failed: {response.status} - {error_text}")
            
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < self.settings.max_retries:
                    logger.warning(f"Vault connection error (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(self.settings.retry_delay * (2 ** attempt))
                    continue
                else:
                    self._metrics["requests_failed"] += 1
                    raise VaultConnectionError(f"Connection failed after {self.settings.max_retries + 1} attempts: {e}")
        
        return None
    
    def _update_avg_response_time(self, response_time: float):
        """Mettre à jour le temps de réponse moyen"""
        if self._metrics["avg_response_time"] == 0.0:
            self._metrics["avg_response_time"] = response_time
        else:
            # Moyenne mobile
            self._metrics["avg_response_time"] = (
                self._metrics["avg_response_time"] * 0.9 + response_time * 0.1
            )
    
    # === API Publique ===
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifier la santé de Vault"""
        try:
            response = await self._request("GET", "/v1/sys/health")
            return {
                "healthy": True,
                "vault_status": response,
                "authenticated": bool(self._token),
                "token_expires": self._token_expires_at.isoformat() if self._token_expires_at else None
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "authenticated": False
            }
    
    async def get_secret(self, path: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Récupérer un secret"""
        await self._ensure_authenticated()
        
        full_path = self.config.get_secret_path(path)
        params = {"version": version} if version else None
        
        response = await self._request("GET", f"/v1/{full_path}", params=params)
        
        if response and "data" in response:
            if self.config.settings.kv_version == "2":
                return response["data"].get("data", {})
            else:
                return response["data"]
        
        return None
    
    async def set_secret(self, path: str, data: Dict[str, Any]) -> bool:
        """Créer ou mettre à jour un secret"""
        await self._ensure_authenticated()
        
        full_path = self.config.get_secret_path(path)
        
        payload = data
        if self.config.settings.kv_version == "2":
            payload = {"data": data}
        
        response = await self._request("POST", f"/v1/{full_path}", data=payload)
        return response is not None
    
    async def delete_secret(self, path: str, versions: Optional[List[int]] = None) -> bool:
        """Supprimer un secret"""
        await self._ensure_authenticated()
        
        if self.config.settings.kv_version == "2":
            if versions:
                # Supprimer versions spécifiques
                metadata_path = self.config.get_secret_metadata_path(path)
                payload = {"versions": versions}
                response = await self._request("POST", f"/v1/{metadata_path}", data=payload)
            else:
                # Soft delete (dernière version)
                full_path = self.config.get_secret_path(path)
                response = await self._request("DELETE", f"/v1/{full_path}")
        else:
            # KV v1 - suppression définitive
            full_path = self.config.get_secret_path(path)
            response = await self._request("DELETE", f"/v1/{full_path}")
        
        return response is not None
    
    async def list_secrets(self, path: str = "") -> List[str]:
        """Lister les secrets dans un chemin"""
        await self._ensure_authenticated()
        
        if self.config.settings.kv_version == "2":
            list_path = f"{self.config.settings.kv_path}/metadata/{path}".rstrip("/")
        else:
            list_path = f"{self.config.settings.kv_path}/{path}".rstrip("/")
        
        response = await self._request("LIST", f"/v1/{list_path}")
        
        if response and "data" in response:
            return response["data"].get("keys", [])
        
        return []
    
    async def encrypt_data(self, plaintext: str, key_name: str = "wakedock") -> Optional[str]:
        """Chiffrer des données avec Transit engine"""
        await self._ensure_authenticated()
        
        import base64
        encoded_plaintext = base64.b64encode(plaintext.encode()).decode()
        
        payload = {"plaintext": encoded_plaintext}
        
        response = await self._request("POST", f"/v1/transit/encrypt/{key_name}", data=payload)
        
        if response and "data" in response:
            return response["data"].get("ciphertext")
        
        return None
    
    async def decrypt_data(self, ciphertext: str, key_name: str = "wakedock") -> Optional[str]:
        """Déchiffrer des données avec Transit engine"""
        await self._ensure_authenticated()
        
        payload = {"ciphertext": ciphertext}
        
        response = await self._request("POST", f"/v1/transit/decrypt/{key_name}", data=payload)
        
        if response and "data" in response:
            import base64
            encoded_plaintext = response["data"].get("plaintext")
            if encoded_plaintext:
                return base64.b64decode(encoded_plaintext).decode()
        
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Récupérer les métriques du client"""
        total_requests = self._metrics["requests_total"]
        success_rate = (
            self._metrics["requests_success"] / total_requests * 100 
            if total_requests > 0 else 0
        )
        
        return {
            **self._metrics,
            "success_rate": round(success_rate, 2),
            "client_config": {
                "auth_method": self.settings.auth_method.value,
                "url": self.settings.url,
                "namespace": self.settings.namespace,
                "kv_version": self.settings.kv_version
            }
        }