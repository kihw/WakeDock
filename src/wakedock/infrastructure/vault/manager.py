"""
Gestionnaire de secrets pour WakeDock avec HashiCorp Vault.

Fournit une interface de haut niveau pour la gestion des secrets,
incluant la rotation automatique, le cache et les templates.
"""

import asyncio
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import secrets
import string

from .client import VaultClient
from .config import VaultConfig

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SecretType(str, Enum):
    """Types de secrets supportés"""
    PASSWORD = "password"
    API_KEY = "api_key"
    DATABASE = "database"
    CERTIFICATE = "certificate"
    SSH_KEY = "ssh_key"
    TOKEN = "token"
    CONFIG = "config"


class RotationStatus(str, Enum):
    """Status de rotation des secrets"""
    ACTIVE = "active"
    ROTATING = "rotating"
    PENDING = "pending"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass
class SecretPolicy:
    """Politique de gestion d'un secret"""
    secret_type: SecretType
    auto_rotate: bool = False
    rotation_interval: timedelta = field(default_factory=lambda: timedelta(days=90))
    max_versions: int = 5
    encryption_required: bool = True
    cache_ttl: int = 300  # 5 minutes
    access_log: bool = True
    notification_enabled: bool = True
    
    # Validation rules
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    complexity_rules: Optional[Dict[str, Any]] = None
    
    # Rotation callback
    rotation_callback: Optional[Callable] = None


@dataclass
class SecretMetadata:
    """Métadonnées d'un secret"""
    path: str
    secret_type: SecretType
    policy: SecretPolicy
    created_at: datetime
    updated_at: datetime
    version: int
    rotation_status: RotationStatus = RotationStatus.ACTIVE
    next_rotation: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire pour stockage"""
        return {
            "path": self.path,
            "secret_type": self.secret_type.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "rotation_status": self.rotation_status.value,
            "next_rotation": self.next_rotation.isoformat() if self.next_rotation else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "access_count": self.access_count,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], policy: SecretPolicy) -> 'SecretMetadata':
        """Créer depuis un dictionnaire"""
        return cls(
            path=data["path"],
            secret_type=SecretType(data["secret_type"]),
            policy=policy,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data["version"],
            rotation_status=RotationStatus(data.get("rotation_status", "active")),
            next_rotation=datetime.fromisoformat(data["next_rotation"]) if data.get("next_rotation") else None,
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None,
            access_count=data.get("access_count", 0),
            tags=data.get("tags", {})
        )


@dataclass
class CachedSecret:
    """Secret en cache avec métadonnées"""
    data: Dict[str, Any]
    metadata: SecretMetadata
    cached_at: datetime
    expires_at: datetime
    encrypted: bool = False
    
    def is_expired(self) -> bool:
        """Vérifier si le cache est expiré"""
        return datetime.now() >= self.expires_at


class SecretTemplate:
    """Template pour la génération de secrets"""
    
    @staticmethod
    def generate_password(
        length: int = 32,
        include_symbols: bool = True,
        exclude_ambiguous: bool = True
    ) -> str:
        """Générer un mot de passe sécurisé"""
        chars = string.ascii_letters + string.digits
        
        if include_symbols:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        if exclude_ambiguous:
            # Exclure caractères ambigus: 0, O, l, 1, I
            chars = chars.replace("0", "").replace("O", "").replace("l", "").replace("1", "").replace("I", "")
        
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    @staticmethod
    def generate_api_key(prefix: str = "wdk", length: int = 32) -> str:
        """Générer une clé API"""
        key_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
        return f"{prefix}_{key_part}"
    
    @staticmethod
    def generate_token(length: int = 64) -> str:
        """Générer un token sécurisé"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_database_credentials(username: str, password_length: int = 24) -> Dict[str, str]:
        """Générer des credentials de base de données"""
        password = SecretTemplate.generate_password(password_length, include_symbols=False)
        return {
            "username": username,
            "password": password,
            "connection_string": f"postgresql://{username}:{password}@localhost:5432/database"
        }


class SecretManager:
    """Gestionnaire principal des secrets"""
    
    def __init__(self, vault_client: VaultClient, config: VaultConfig):
        self.vault = vault_client
        self.config = config
        self._cache: Dict[str, CachedSecret] = {}
        self._policies: Dict[str, SecretPolicy] = {}
        self._rotation_tasks: Dict[str, asyncio.Task] = {}
        self._metrics = {
            "secrets_created": 0,
            "secrets_accessed": 0,
            "secrets_rotated": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "rotation_failures": 0
        }
        
        # Politiques par défaut
        self._setup_default_policies()
    
    def _setup_default_policies(self):
        """Configurer les politiques par défaut"""
        self._policies.update({
            "database": SecretPolicy(
                secret_type=SecretType.DATABASE,
                auto_rotate=True,
                rotation_interval=timedelta(days=30),
                max_versions=3,
                min_length=16,
                complexity_rules={"require_special": False}
            ),
            "api_key": SecretPolicy(
                secret_type=SecretType.API_KEY,
                auto_rotate=True,
                rotation_interval=timedelta(days=90),
                max_versions=2
            ),
            "password": SecretPolicy(
                secret_type=SecretType.PASSWORD,
                auto_rotate=False,
                rotation_interval=timedelta(days=180),
                max_versions=5,
                min_length=12,
                complexity_rules={"require_special": True, "require_numbers": True}
            ),
            "certificate": SecretPolicy(
                secret_type=SecretType.CERTIFICATE,
                auto_rotate=True,
                rotation_interval=timedelta(days=60),
                max_versions=2,
                encryption_required=True
            ),
            "config": SecretPolicy(
                secret_type=SecretType.CONFIG,
                auto_rotate=False,
                cache_ttl=600,  # 10 minutes
                encryption_required=False
            )
        })
    
    async def create_secret(
        self,
        path: str,
        data: Union[Dict[str, Any], str],
        secret_type: SecretType = SecretType.CONFIG,
        policy_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        auto_generate: bool = False
    ) -> bool:
        """Créer un nouveau secret"""
        try:
            # Récupérer la politique
            policy = self._get_policy(policy_name or secret_type.value)
            
            # Auto-génération si demandée
            if auto_generate:
                if secret_type == SecretType.PASSWORD:
                    length = policy.complexity_rules.get("length", 24) if policy.complexity_rules else 24
                    data = {"password": SecretTemplate.generate_password(length)}
                elif secret_type == SecretType.API_KEY:
                    data = {"api_key": SecretTemplate.generate_api_key()}
                elif secret_type == SecretType.TOKEN:
                    data = {"token": SecretTemplate.generate_token()}
                elif secret_type == SecretType.DATABASE:
                    if isinstance(data, dict) and "username" in data:
                        data = SecretTemplate.generate_database_credentials(data["username"])
                    else:
                        raise ValueError("Database secret requires username for auto-generation")
            
            # Normaliser les données
            if isinstance(data, str):
                data = {"value": data}
            
            # Validation
            if not self._validate_secret_data(data, policy):
                raise ValueError("Secret data validation failed")
            
            # Créer métadonnées
            now = datetime.now()
            metadata = SecretMetadata(
                path=path,
                secret_type=secret_type,
                policy=policy,
                created_at=now,
                updated_at=now,
                version=1,
                tags=tags or {}
            )
            
            # Programmer rotation si nécessaire
            if policy.auto_rotate:
                metadata.next_rotation = now + policy.rotation_interval
            
            # Sauvegarder le secret
            secret_data = {
                "_metadata": metadata.to_dict(),
                **data
            }
            
            success = await self.vault.set_secret(path, secret_data)
            
            if success:
                self._metrics["secrets_created"] += 1
                
                # Invalider le cache
                self._invalidate_cache(path)
                
                # Programmer la rotation
                if policy.auto_rotate:
                    self._schedule_rotation(path, metadata.next_rotation)
                
                logger.info(f"Secret created: {path} (type: {secret_type.value})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to create secret {path}: {e}")
            return False
    
    async def get_secret(
        self,
        path: str,
        version: Optional[int] = None,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Récupérer un secret"""
        try:
            # Vérifier le cache d'abord
            if use_cache and version is None:
                cached = self._get_from_cache(path)
                if cached:
                    self._metrics["cache_hits"] += 1
                    await self._update_access_metadata(path, cached.metadata)
                    return self._filter_metadata(cached.data)
            
            self._metrics["cache_misses"] += 1
            
            # Récupérer depuis Vault
            secret_data = await self.vault.get_secret(path, version)
            
            if secret_data:
                self._metrics["secrets_accessed"] += 1
                
                # Extraire métadonnées
                metadata_dict = secret_data.pop("_metadata", {})
                if metadata_dict:
                    policy = self._get_policy(metadata_dict.get("secret_type", "config"))
                    metadata = SecretMetadata.from_dict(metadata_dict, policy)
                    
                    # Mettre en cache
                    if use_cache and version is None:
                        self._put_in_cache(path, secret_data, metadata)
                    
                    # Mettre à jour les stats d'accès
                    await self._update_access_metadata(path, metadata)
                
                return self._filter_metadata(secret_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get secret {path}: {e}")
            return None
    
    async def update_secret(
        self,
        path: str,
        data: Union[Dict[str, Any], str],
        merge: bool = False
    ) -> bool:
        """Mettre à jour un secret"""
        try:
            # Récupérer secret existant pour métadonnées
            existing = await self.vault.get_secret(path)
            if not existing:
                logger.error(f"Secret {path} not found for update")
                return False
            
            # Extraire métadonnées
            metadata_dict = existing.get("_metadata", {})
            if not metadata_dict:
                logger.error(f"No metadata found for secret {path}")
                return False
            
            policy = self._get_policy(metadata_dict.get("secret_type", "config"))
            metadata = SecretMetadata.from_dict(metadata_dict, policy)
            
            # Préparer nouvelles données
            if isinstance(data, str):
                data = {"value": data}
            
            if merge:
                # Merger avec données existantes
                filtered_existing = self._filter_metadata(existing)
                filtered_existing.update(data)
                data = filtered_existing
            
            # Validation
            if not self._validate_secret_data(data, policy):
                raise ValueError("Secret data validation failed")
            
            # Mettre à jour métadonnées
            metadata.updated_at = datetime.now()
            metadata.version += 1
            
            # Programmer prochaine rotation si auto-rotate
            if policy.auto_rotate:
                metadata.next_rotation = metadata.updated_at + policy.rotation_interval
            
            # Sauvegarder
            secret_data = {
                "_metadata": metadata.to_dict(),
                **data
            }
            
            success = await self.vault.set_secret(path, secret_data)
            
            if success:
                # Invalider le cache
                self._invalidate_cache(path)
                
                # Reprogrammer rotation
                if policy.auto_rotate:
                    self._schedule_rotation(path, metadata.next_rotation)
                
                logger.info(f"Secret updated: {path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update secret {path}: {e}")
            return False
    
    async def rotate_secret(self, path: str, force: bool = False) -> bool:
        """Effectuer la rotation d'un secret"""
        try:
            # Récupérer secret existant
            existing = await self.vault.get_secret(path)
            if not existing:
                logger.error(f"Secret {path} not found for rotation")
                return False
            
            # Extraire métadonnées
            metadata_dict = existing.get("_metadata", {})
            if not metadata_dict:
                logger.error(f"No metadata found for secret {path}")
                return False
            
            policy = self._get_policy(metadata_dict.get("secret_type", "config"))
            metadata = SecretMetadata.from_dict(metadata_dict, policy)
            
            # Vérifier si rotation nécessaire
            if not force and not policy.auto_rotate:
                logger.info(f"Secret {path} does not have auto-rotation enabled")
                return False
            
            if not force and metadata.next_rotation and datetime.now() < metadata.next_rotation:
                logger.info(f"Secret {path} not due for rotation yet")
                return False
            
            # Marquer comme en cours de rotation
            metadata.rotation_status = RotationStatus.ROTATING
            await self._save_metadata(path, existing, metadata)
            
            # Générer nouvelles données selon le type
            new_data = await self._generate_rotated_data(metadata.secret_type, existing)
            
            if not new_data:
                logger.error(f"Failed to generate rotated data for {path}")
                metadata.rotation_status = RotationStatus.FAILED
                await self._save_metadata(path, existing, metadata)
                self._metrics["rotation_failures"] += 1
                return False
            
            # Callback de pré-rotation si défini
            if policy.rotation_callback:
                try:
                    await policy.rotation_callback(path, existing, new_data)
                except Exception as e:
                    logger.error(f"Rotation callback failed for {path}: {e}")
                    metadata.rotation_status = RotationStatus.FAILED
                    await self._save_metadata(path, existing, metadata)
                    return False
            
            # Mettre à jour le secret
            success = await self.update_secret(path, new_data)
            
            if success:
                metadata.rotation_status = RotationStatus.ACTIVE
                metadata.next_rotation = datetime.now() + policy.rotation_interval
                self._metrics["secrets_rotated"] += 1
                
                logger.info(f"Secret rotated successfully: {path}")
                return True
            else:
                metadata.rotation_status = RotationStatus.FAILED
                self._metrics["rotation_failures"] += 1
                return False
            
        except Exception as e:
            logger.error(f"Failed to rotate secret {path}: {e}")
            self._metrics["rotation_failures"] += 1
            return False
    
    async def delete_secret(self, path: str, permanent: bool = False) -> bool:
        """Supprimer un secret"""
        try:
            # Annuler rotation programmée
            if path in self._rotation_tasks:
                self._rotation_tasks[path].cancel()
                del self._rotation_tasks[path]
            
            # Invalider le cache
            self._invalidate_cache(path)
            
            # Supprimer de Vault
            if permanent and self.config.settings.kv_version == "2":
                # Supprimer toutes les versions
                versions = await self._get_all_versions(path)
                success = await self.vault.delete_secret(path, versions)
            else:
                # Soft delete
                success = await self.vault.delete_secret(path)
            
            if success:
                logger.info(f"Secret deleted: {path} (permanent: {permanent})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete secret {path}: {e}")
            return False
    
    async def list_secrets(self, path: str = "", include_metadata: bool = False) -> List[Union[str, Dict[str, Any]]]:
        """Lister les secrets"""
        try:
            secret_paths = await self.vault.list_secrets(path)
            
            if not include_metadata:
                return secret_paths
            
            # Récupérer métadonnées pour chaque secret
            results = []
            for secret_path in secret_paths:
                full_path = f"{path}/{secret_path}".strip("/")
                secret_data = await self.vault.get_secret(full_path)
                
                if secret_data and "_metadata" in secret_data:
                    metadata_dict = secret_data["_metadata"]
                    results.append({
                        "path": full_path,
                        "metadata": metadata_dict
                    })
                else:
                    results.append({
                        "path": full_path,
                        "metadata": None
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to list secrets at {path}: {e}")
            return []
    
    # === Méthodes privées ===
    
    def _get_policy(self, policy_name: str) -> SecretPolicy:
        """Récupérer une politique"""
        return self._policies.get(policy_name, self._policies["config"])
    
    def _validate_secret_data(self, data: Dict[str, Any], policy: SecretPolicy) -> bool:
        """Valider les données d'un secret"""
        if not data:
            return False
        
        # Vérifications de base selon le type
        if policy.secret_type == SecretType.PASSWORD and "password" in data:
            password = data["password"]
            if policy.min_length and len(password) < policy.min_length:
                return False
            if policy.max_length and len(password) > policy.max_length:
                return False
            
            # Règles de complexité
            if policy.complexity_rules:
                if policy.complexity_rules.get("require_numbers") and not any(c.isdigit() for c in password):
                    return False
                if policy.complexity_rules.get("require_special") and not any(c in "!@#$%^&*()_+-=" for c in password):
                    return False
        
        return True
    
    def _filter_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filtrer les métadonnées internes"""
        return {k: v for k, v in data.items() if not k.startswith("_")}
    
    def _get_from_cache(self, path: str) -> Optional[CachedSecret]:
        """Récupérer depuis le cache"""
        cached = self._cache.get(path)
        if cached and not cached.is_expired():
            return cached
        elif cached:
            # Supprimer entrée expirée
            del self._cache[path]
        return None
    
    def _put_in_cache(self, path: str, data: Dict[str, Any], metadata: SecretMetadata):
        """Mettre en cache"""
        if not metadata.policy.cache_ttl:
            return
        
        now = datetime.now()
        expires_at = now + timedelta(seconds=metadata.policy.cache_ttl)
        
        cached = CachedSecret(
            data=data.copy(),
            metadata=metadata,
            cached_at=now,
            expires_at=expires_at,
            encrypted=metadata.policy.encryption_required
        )
        
        self._cache[path] = cached
    
    def _invalidate_cache(self, path: str):
        """Invalider le cache"""
        if path in self._cache:
            del self._cache[path]
    
    async def _update_access_metadata(self, path: str, metadata: SecretMetadata):
        """Mettre à jour les métadonnées d'accès"""
        metadata.last_accessed = datetime.now()
        metadata.access_count += 1
        
        # Sauvegarder périodiquement (tous les 10 accès)
        if metadata.access_count % 10 == 0:
            try:
                existing = await self.vault.get_secret(path)
                if existing:
                    await self._save_metadata(path, existing, metadata)
            except Exception as e:
                logger.warning(f"Failed to update access metadata for {path}: {e}")
    
    async def _save_metadata(self, path: str, data: Dict[str, Any], metadata: SecretMetadata):
        """Sauvegarder les métadonnées"""
        data["_metadata"] = metadata.to_dict()
        await self.vault.set_secret(path, data)
    
    async def _generate_rotated_data(self, secret_type: SecretType, existing_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Générer nouvelles données pour rotation"""
        if secret_type == SecretType.PASSWORD:
            return {"password": SecretTemplate.generate_password()}
        
        elif secret_type == SecretType.API_KEY:
            return {"api_key": SecretTemplate.generate_api_key()}
        
        elif secret_type == SecretType.TOKEN:
            return {"token": SecretTemplate.generate_token()}
        
        elif secret_type == SecretType.DATABASE:
            username = existing_data.get("username")
            if username:
                return SecretTemplate.generate_database_credentials(username)
        
        # Pour les autres types, pas de rotation automatique
        return None
    
    def _schedule_rotation(self, path: str, next_rotation: Optional[datetime]):
        """Programmer la rotation d'un secret"""
        if not next_rotation:
            return
        
        # Annuler rotation existante
        if path in self._rotation_tasks:
            self._rotation_tasks[path].cancel()
        
        # Calculer délai
        delay = (next_rotation - datetime.now()).total_seconds()
        if delay <= 0:
            delay = 60  # Minimum 1 minute
        
        # Programmer nouvelle rotation
        async def rotation_task():
            await asyncio.sleep(delay)
            await self.rotate_secret(path)
        
        self._rotation_tasks[path] = asyncio.create_task(rotation_task())
    
    async def _get_all_versions(self, path: str) -> List[int]:
        """Récupérer toutes les versions d'un secret"""
        try:
            if self.config.settings.kv_version == "2":
                metadata_path = self.config.get_secret_metadata_path(path)
                response = await self.vault._request("GET", f"/v1/{metadata_path}")
                if response and "data" in response:
                    versions = response["data"].get("versions", {})
                    return list(versions.keys())
            return [1]  # KV v1 n'a qu'une version
        except Exception:
            return []
    
    # === API publique ===
    
    def add_policy(self, name: str, policy: SecretPolicy):
        """Ajouter une politique personnalisée"""
        self._policies[name] = policy
    
    def get_metrics(self) -> Dict[str, Any]:
        """Récupérer les métriques"""
        return {
            **self._metrics,
            "cache_size": len(self._cache),
            "active_rotations": len(self._rotation_tasks),
            "policies_count": len(self._policies)
        }
    
    async def cleanup_cache(self):
        """Nettoyer le cache expiré"""
        expired_keys = [
            path for path, cached in self._cache.items()
            if cached.is_expired()
        ]
        
        for path in expired_keys:
            del self._cache[path]
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def force_rotation_check(self):
        """Forcer la vérification des rotations"""
        secrets = await self.list_secrets(include_metadata=True)
        
        for secret_info in secrets:
            if isinstance(secret_info, dict) and secret_info.get("metadata"):
                metadata_dict = secret_info["metadata"]
                next_rotation = metadata_dict.get("next_rotation")
                
                if next_rotation:
                    next_rotation_dt = datetime.fromisoformat(next_rotation)
                    if datetime.now() >= next_rotation_dt:
                        path = secret_info["path"]
                        logger.info(f"Secret {path} is due for rotation")
                        await self.rotate_secret(path)