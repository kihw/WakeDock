"""
API endpoints pour la gestion des secrets avec HashiCorp Vault.

Fournit une interface REST pour créer, récupérer, mettre à jour
et supprimer des secrets de manière sécurisée.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import PlainTextResponse
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
import logging

from wakedock.infrastructure.vault.service import get_vault_service, VaultService
from wakedock.infrastructure.vault.manager import SecretType, SecretPolicy
from wakedock.infrastructure.vault.monitor import EventType, AlertLevel
from wakedock.api.auth.dependencies import get_current_user, require_admin
from wakedock.database.models import User, UserRole

logger = logging.getLogger(__name__)

router = APIRouter()


# === Models Pydantic ===

class SecretCreateRequest(BaseModel):
    """Requête de création de secret"""
    path: str = Field(..., description="Chemin du secret", min_length=1)
    data: Union[Dict[str, Any], str] = Field(..., description="Données du secret")
    secret_type: SecretType = Field(SecretType.CONFIG, description="Type de secret")
    tags: Optional[Dict[str, str]] = Field(None, description="Tags métadonnées")
    auto_generate: bool = Field(False, description="Auto-générer le secret")
    auto_rotate: bool = Field(False, description="Activer la rotation automatique")
    
    @validator("path")
    def validate_path(cls, v):
        if v.startswith("/"):
            v = v[1:]
        if not v or v.endswith("/"):
            raise ValueError("Invalid path format")
        return v


class SecretUpdateRequest(BaseModel):
    """Requête de mise à jour de secret"""
    data: Union[Dict[str, Any], str] = Field(..., description="Nouvelles données")
    merge: bool = Field(False, description="Fusionner avec données existantes")


class SecretResponse(BaseModel):
    """Réponse contenant un secret"""
    path: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    retrieved_at: datetime = Field(default_factory=datetime.now)


class SecretListResponse(BaseModel):
    """Réponse de liste de secrets"""
    secrets: List[Union[str, Dict[str, Any]]]
    total: int
    path: str


class VaultHealthResponse(BaseModel):
    """Réponse de santé Vault"""
    healthy: bool
    vault_health: Dict[str, Any]
    service_metrics: Dict[str, Any]
    initialized: bool


class VaultMetricsResponse(BaseModel):
    """Réponse des métriques Vault"""
    service: Dict[str, Any]
    vault_client: Dict[str, Any]
    secret_manager: Dict[str, Any]
    monitor: Dict[str, Any]


class EncryptRequest(BaseModel):
    """Requête de chiffrement"""
    plaintext: str = Field(..., description="Données à chiffrer")
    key_name: str = Field("wakedock", description="Nom de la clé de chiffrement")


class DecryptRequest(BaseModel):
    """Requête de déchiffrement"""
    ciphertext: str = Field(..., description="Données chiffrées")
    key_name: str = Field("wakedock", description="Nom de la clé de chiffrement")


class RotationRequest(BaseModel):
    """Requête de rotation de secret"""
    force: bool = Field(False, description="Forcer la rotation")


# === Dependencies ===

def get_vault_service_dep(request: Request) -> VaultService:
    """Dependency pour récupérer le service Vault"""
    vault_service = getattr(request.app.state, 'vault_service', None)
    if vault_service is None:
        vault_service = get_vault_service()
    
    if not vault_service.is_initialized():
        raise HTTPException(
            status_code=503,
            detail="Vault service not initialized"
        )
    
    return vault_service


def require_vault_enabled(vault_service: VaultService = Depends(get_vault_service_dep)):
    """Dependency pour vérifier que Vault est activé"""
    if not vault_service.settings.enabled:
        raise HTTPException(
            status_code=503,
            detail="Vault integration is disabled"
        )
    return vault_service


# === Endpoints Santé et Status ===

@router.get("/health", response_model=VaultHealthResponse, summary="Vault Health Check")
async def vault_health(vault_service: VaultService = Depends(get_vault_service_dep)):
    """
    Vérifier la santé de l'intégration Vault.
    """
    try:
        health = await vault_service.health_check()
        return VaultHealthResponse(**health)
    except Exception as e:
        logger.error(f"Vault health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Vault health check failed: {str(e)}"
        )


@router.get("/metrics", response_model=VaultMetricsResponse, summary="Vault Metrics")
async def vault_metrics(
    vault_service: VaultService = Depends(require_vault_enabled),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer les métriques complètes de Vault.
    """
    try:
        metrics = vault_service.get_metrics()
        return VaultMetricsResponse(**metrics)
    except Exception as e:
        logger.error(f"Failed to get Vault metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve Vault metrics"
        )


@router.get("/metrics/prometheus", summary="Vault Prometheus Metrics")
async def vault_prometheus_metrics(
    vault_service: VaultService = Depends(require_vault_enabled),
    current_user: User = Depends(get_current_user)
):
    """
    Exporter les métriques Vault au format Prometheus.
    """
    try:
        metrics = await vault_service.export_prometheus_metrics()
        return PlainTextResponse(
            content=metrics,
            media_type="text/plain; version=0.0.4"
        )
    except Exception as e:
        logger.error(f"Failed to export Prometheus metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to export Prometheus metrics"
        )


# === Endpoints Gestion des Secrets ===

@router.post("/secrets", response_model=Dict[str, Any], summary="Create Secret")
async def create_secret(
    request: SecretCreateRequest,
    vault_service: VaultService = Depends(require_vault_enabled),
    current_user: User = Depends(get_current_user)
):
    """
    Créer un nouveau secret dans Vault.
    
    Supporte l'auto-génération de mots de passe, clés API, etc.
    """
    try:
        # Vérifier permissions
        if not _has_secret_permission(current_user, request.path, "create"):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to create secret"
            )
        
        # Créer le secret
        success = await vault_service.create_secret(
            path=request.path,
            data=request.data,
            secret_type=request.secret_type,
            tags=request.tags,
            auto_generate=request.auto_generate
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to create secret"
            )
        
        # Log de l'opération
        if vault_service.monitor:
            await vault_service.monitor.log_secret_operation(
                "create",
                request.path,
                user=current_user.username,
                details={
                    "secret_type": request.secret_type.value,
                    "auto_generated": request.auto_generate
                }
            )
        
        return {
            "success": True,
            "message": f"Secret created at {request.path}",
            "path": request.path,
            "secret_type": request.secret_type.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create secret {request.path}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal error while creating secret"
        )


@router.get("/secrets/{path:path}", response_model=SecretResponse, summary="Get Secret")
async def get_secret(
    path: str,
    version: Optional[int] = Query(None, description="Version spécifique du secret"),
    use_cache: bool = Query(True, description="Utiliser le cache"),
    vault_service: VaultService = Depends(require_vault_enabled),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer un secret depuis Vault.
    """
    try:
        # Vérifier permissions
        if not _has_secret_permission(current_user, path, "read"):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to read secret"
            )
        
        # Récupérer le secret
        secret_data = await vault_service.get_secret(
            path=path,
            version=version,
            use_cache=use_cache
        )
        
        if secret_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"Secret not found at {path}"
            )
        
        return SecretResponse(
            path=path,
            data=secret_data,
            metadata=secret_data.get("_metadata") if "_metadata" in secret_data else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get secret {path}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal error while retrieving secret"
        )


@router.put("/secrets/{path:path}", response_model=Dict[str, Any], summary="Update Secret")
async def update_secret(
    path: str,
    request: SecretUpdateRequest,
    vault_service: VaultService = Depends(require_vault_enabled),
    current_user: User = Depends(get_current_user)
):
    """
    Mettre à jour un secret existant.
    """
    try:
        # Vérifier permissions
        if not _has_secret_permission(current_user, path, "update"):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to update secret"
            )
        
        # Mettre à jour le secret
        success = await vault_service.update_secret(
            path=path,
            data=request.data,
            merge=request.merge
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update secret"
            )
        
        return {
            "success": True,
            "message": f"Secret updated at {path}",
            "path": path,
            "merged": request.merge
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update secret {path}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal error while updating secret"
        )


@router.delete("/secrets/{path:path}", response_model=Dict[str, Any], summary="Delete Secret")
async def delete_secret(
    path: str,
    permanent: bool = Query(False, description="Suppression permanente"),
    vault_service: VaultService = Depends(require_vault_enabled),
    current_user: User = Depends(get_current_user)
):
    """
    Supprimer un secret.
    """
    try:
        # Vérifier permissions (admin requis pour suppression permanente)
        if permanent and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=403,
                detail="Admin privileges required for permanent deletion"
            )
        
        if not _has_secret_permission(current_user, path, "delete"):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to delete secret"
            )
        
        # Supprimer le secret
        success = await vault_service.delete_secret(
            path=path,
            permanent=permanent
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete secret"
            )
        
        return {
            "success": True,
            "message": f"Secret deleted at {path}",
            "path": path,
            "permanent": permanent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete secret {path}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal error while deleting secret"
        )


@router.get("/secrets", response_model=SecretListResponse, summary="List Secrets")
async def list_secrets(
    path: str = Query("", description="Chemin de base pour la liste"),
    include_metadata: bool = Query(False, description="Inclure les métadonnées"),
    vault_service: VaultService = Depends(require_vault_enabled),
    current_user: User = Depends(get_current_user)
):
    """
    Lister les secrets dans un chemin donné.
    """
    try:
        # Vérifier permissions
        if not _has_secret_permission(current_user, path, "list"):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to list secrets"
            )
        
        # Lister les secrets
        secrets = await vault_service.list_secrets(
            path=path,
            include_metadata=include_metadata
        )
        
        return SecretListResponse(
            secrets=secrets,
            total=len(secrets),
            path=path
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list secrets at {path}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal error while listing secrets"
        )


# === Endpoints Rotation ===

@router.post("/secrets/{path:path}/rotate", response_model=Dict[str, Any], summary="Rotate Secret")
async def rotate_secret(
    path: str,
    request: RotationRequest,
    vault_service: VaultService = Depends(require_vault_enabled),
    current_user: User = Depends(get_current_user)
):
    """
    Effectuer la rotation d'un secret.
    """
    try:
        # Vérifier permissions
        if not _has_secret_permission(current_user, path, "rotate"):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to rotate secret"
            )
        
        # Effectuer la rotation
        success = await vault_service.rotate_secret(
            path=path,
            force=request.force
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to rotate secret"
            )
        
        return {
            "success": True,
            "message": f"Secret rotated at {path}",
            "path": path,
            "forced": request.force
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rotate secret {path}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal error while rotating secret"
        )


# === Endpoints Chiffrement ===

@router.post("/encrypt", response_model=Dict[str, str], summary="Encrypt Data")
async def encrypt_data(
    request: EncryptRequest,
    vault_service: VaultService = Depends(require_vault_enabled),
    current_user: User = Depends(get_current_user)
):
    """
    Chiffrer des données avec Vault Transit engine.
    """
    try:
        ciphertext = await vault_service.encrypt_data(
            request.plaintext,
            request.key_name
        )
        
        if ciphertext is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to encrypt data"
            )
        
        return {
            "ciphertext": ciphertext,
            "key_name": request.key_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to encrypt data: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal error while encrypting data"
        )


@router.post("/decrypt", response_model=Dict[str, str], summary="Decrypt Data")
async def decrypt_data(
    request: DecryptRequest,
    vault_service: VaultService = Depends(require_vault_enabled),
    current_user: User = Depends(get_current_user)
):
    """
    Déchiffrer des données avec Vault Transit engine.
    """
    try:
        plaintext = await vault_service.decrypt_data(
            request.ciphertext,
            request.key_name
        )
        
        if plaintext is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to decrypt data"
            )
        
        return {
            "plaintext": plaintext,
            "key_name": request.key_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to decrypt data: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal error while decrypting data"
        )


# === Endpoints Events et Audit ===

@router.get("/events", summary="Get Vault Events")
async def get_vault_events(
    event_type: Optional[str] = Query(None, description="Type d'événement"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'événements"),
    vault_service: VaultService = Depends(require_vault_enabled),
    current_user: User = Depends(require_admin)
):
    """
    Récupérer les événements d'audit Vault.
    
    Nécessite les droits administrateur.
    """
    try:
        # Convertir event_type si fourni
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = EventType(event_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid event type: {event_type}"
                )
        
        events = vault_service.get_events(
            event_type=event_type_enum,
            limit=limit
        )
        
        return {
            "events": events,
            "total": len(events),
            "filters": {
                "event_type": event_type,
                "limit": limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Vault events: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal error while retrieving events"
        )


# === Fonctions utilitaires ===

def _has_secret_permission(user: User, path: str, operation: str) -> bool:
    """Vérifier les permissions d'accès aux secrets"""
    # Admin a tous les droits
    if user.role == UserRole.ADMIN:
        return True
    
    # Users peuvent accéder à leurs propres secrets
    user_prefix = f"users/{user.username}/"
    if path.startswith(user_prefix):
        return True
    
    # Secrets publics en lecture seule pour tous
    if path.startswith("public/") and operation == "read":
        return True
    
    # Autres vérifications selon la logique métier
    # À adapter selon les besoins de sécurité
    
    return False