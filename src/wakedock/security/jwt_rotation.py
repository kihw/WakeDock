"""
JWT Token Rotation Service
Implémente la rotation automatique des tokens JWT pour améliorer la sécurité
"""

import asyncio
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"

@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime

class JWTRotationService:
    """Service de rotation automatique des tokens JWT"""
    
    def __init__(self, 
                 secret_key: str,
                 algorithm: str = "HS256",
                 access_token_expire_minutes: int = 30,
                 refresh_token_expire_days: int = 7,
                 rotation_threshold_minutes: int = 5):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.rotation_threshold_minutes = rotation_threshold_minutes
        
        # Cache des tokens révoqués
        self.revoked_tokens: set = set()
        
        # Statistiques
        self.rotation_stats = {
            "total_rotations": 0,
            "successful_rotations": 0,
            "failed_rotations": 0,
            "last_rotation": None
        }
    
    def _create_token(self, 
                      user_id: int, 
                      token_type: TokenType,
                      expires_delta: timedelta,
                      additional_claims: Optional[Dict[str, Any]] = None) -> Tuple[str, datetime]:
        """Crée un token JWT avec les claims spécifiés"""
        
        now = datetime.now(timezone.utc)
        expires_at = now + expires_delta
        
        payload = {
            "user_id": user_id,
            "type": token_type.value,
            "iat": now,
            "exp": expires_at,
            "jti": f"{user_id}_{token_type.value}_{int(now.timestamp())}"  # Unique token ID
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token, expires_at
    
    def create_token_pair(self, user_id: int, **additional_claims) -> TokenPair:
        """Crée une paire de tokens access/refresh"""
        
        access_token, access_expires_at = self._create_token(
            user_id, 
            TokenType.ACCESS, 
            timedelta(minutes=self.access_token_expire_minutes),
            additional_claims
        )
        
        refresh_token, refresh_expires_at = self._create_token(
            user_id, 
            TokenType.REFRESH, 
            timedelta(days=self.refresh_token_expire_days),
            additional_claims
        )
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at
        )
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Décode et valide un token JWT"""
        try:
            # Vérifier si le token est révoqué
            if token in self.revoked_tokens:
                logger.warning("Tentative d'utilisation d'un token révoqué")
                return None
            
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Vérifier le type de token
            if "type" not in payload:
                logger.warning("Token sans type spécifié")
                return None
            
            # Vérifier la validité temporelle
            now = datetime.now(timezone.utc)
            if payload.get("exp") and datetime.fromtimestamp(payload["exp"], timezone.utc) < now:
                logger.debug("Token expiré")
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.debug("Token expiré")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token invalide: {e}")
            return None
    
    def should_rotate_token(self, token: str) -> bool:
        """Détermine si un token devrait être tourné"""
        
        payload = self.decode_token(token)
        if not payload:
            return False
        
        # Vérifier si le token est proche de l'expiration
        exp_timestamp = payload.get("exp")
        if not exp_timestamp:
            return False
        
        exp_time = datetime.fromtimestamp(exp_timestamp, timezone.utc)
        now = datetime.now(timezone.utc)
        time_until_expiry = exp_time - now
        
        # Tourner si moins de X minutes avant expiration
        return time_until_expiry.total_seconds() <= (self.rotation_threshold_minutes * 60)
    
    async def rotate_tokens(self, 
                           refresh_token: str,
                           db: AsyncSession) -> Optional[TokenPair]:
        """Effectue la rotation des tokens"""
        
        try:
            # Valider le refresh token
            refresh_payload = self.decode_token(refresh_token)
            if not refresh_payload or refresh_payload.get("type") != TokenType.REFRESH.value:
                logger.warning("Refresh token invalide pour la rotation")
                return None
            
            user_id = refresh_payload.get("user_id")
            if not user_id:
                logger.warning("Refresh token sans user_id")
                return None
            
            # Révoquer l'ancien refresh token
            self.revoke_token(refresh_token)
            
            # Créer nouvelle paire de tokens
            new_tokens = self.create_token_pair(user_id)
            
            # Sauvegarder dans la base de données
            await self._save_token_rotation(db, user_id, new_tokens)
            
            # Mettre à jour les statistiques
            self.rotation_stats["total_rotations"] += 1
            self.rotation_stats["successful_rotations"] += 1
            self.rotation_stats["last_rotation"] = datetime.now(timezone.utc)
            
            logger.info(f"Rotation réussie pour l'utilisateur {user_id}")
            return new_tokens
            
        except Exception as e:
            logger.error(f"Erreur lors de la rotation des tokens: {e}")
            self.rotation_stats["failed_rotations"] += 1
            return None
    
    def revoke_token(self, token: str) -> None:
        """Révoque un token (l'ajoute à la liste noire)"""
        self.revoked_tokens.add(token)
        logger.debug(f"Token révoqué")
    
    def revoke_all_user_tokens(self, user_id: int) -> None:
        """Révoque tous les tokens d'un utilisateur"""
        # Dans une implémentation complète, ceci nécessiterait une base de données
        # pour tracker tous les tokens par utilisateur
        logger.info(f"Révocation de tous les tokens pour l'utilisateur {user_id}")
    
    async def _save_token_rotation(self, 
                                  db: AsyncSession, 
                                  user_id: int, 
                                  tokens: TokenPair) -> None:
        """Sauvegarde la rotation dans la base de données"""
        
        # Ici, nous pourrions sauvegarder les métadonnées de rotation
        # Par exemple, dans une table d'audit des tokens
        try:
            # Exemple d'insertion dans une table d'audit
            audit_entry = {
                "user_id": user_id,
                "action": "token_rotation",
                "timestamp": datetime.now(timezone.utc),
                "access_token_expires": tokens.access_expires_at,
                "refresh_token_expires": tokens.refresh_expires_at
            }
            
            # Insert dans la table d'audit (à adapter selon votre schéma)
            # await db.execute(insert(TokenAudit).values(audit_entry))
            # await db.commit()
            
            logger.debug(f"Rotation sauvegardée pour l'utilisateur {user_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la rotation: {e}")
    
    async def cleanup_expired_tokens(self) -> None:
        """Nettoie les tokens expirés du cache de révocation"""
        
        now = datetime.now(timezone.utc)
        tokens_to_remove = []
        
        for token in self.revoked_tokens:
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
                exp_timestamp = payload.get("exp")
                if exp_timestamp and datetime.fromtimestamp(exp_timestamp, timezone.utc) < now:
                    tokens_to_remove.append(token)
            except jwt.InvalidTokenError:
                # Token invalide, le supprimer
                tokens_to_remove.append(token)
        
        for token in tokens_to_remove:
            self.revoked_tokens.discard(token)
        
        if tokens_to_remove:
            logger.info(f"Nettoyage de {len(tokens_to_remove)} tokens expirés")
    
    async def start_background_cleanup(self, interval_minutes: int = 60) -> None:
        """Démarre le nettoyage automatique en arrière-plan"""
        
        while True:
            try:
                await asyncio.sleep(interval_minutes * 60)
                await self.cleanup_expired_tokens()
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage automatique: {e}")
    
    def get_rotation_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de rotation"""
        return {
            **self.rotation_stats,
            "revoked_tokens_count": len(self.revoked_tokens),
            "rotation_threshold_minutes": self.rotation_threshold_minutes
        }


class JWTRotationManager:
    """Manager pour la rotation JWT avec intégration à l'application"""
    
    def __init__(self, jwt_rotation_service: JWTRotationService):
        self.rotation_service = jwt_rotation_service
        self._background_task = None
    
    async def start(self) -> None:
        """Démarre le service de rotation"""
        if self._background_task is None:
            self._background_task = asyncio.create_task(
                self.rotation_service.start_background_cleanup()
            )
            logger.info("Service de rotation JWT démarré")
    
    async def stop(self) -> None:
        """Arrête le service de rotation"""
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
            self._background_task = None
            logger.info("Service de rotation JWT arrêté")
    
    async def handle_token_rotation(self, 
                                   refresh_token: str,
                                   db: AsyncSession) -> Optional[TokenPair]:
        """Gère la rotation des tokens avec vérification"""
        
        if self.rotation_service.should_rotate_token(refresh_token):
            return await self.rotation_service.rotate_tokens(refresh_token, db)
        
        return None


# Instance globale
jwt_rotation_service = None
jwt_rotation_manager = None

def get_jwt_rotation_service() -> JWTRotationService:
    """Obtient l'instance du service de rotation JWT"""
    global jwt_rotation_service
    if jwt_rotation_service is None:
        # Configuration par défaut, à adapter selon votre config
        jwt_rotation_service = JWTRotationService(
            secret_key="your-secret-key",  # À charger depuis la configuration
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7,
            rotation_threshold_minutes=5
        )
    return jwt_rotation_service

def get_jwt_rotation_manager() -> JWTRotationManager:
    """Obtient l'instance du manager de rotation JWT"""
    global jwt_rotation_manager
    if jwt_rotation_manager is None:
        jwt_rotation_manager = JWTRotationManager(get_jwt_rotation_service())
    return jwt_rotation_manager
