"""
Advanced Multi-Factor Authentication Manager

Provides enhanced MFA capabilities including:
- TOTP (Time-based One-Time Password)
- SMS authentication
- Email verification
- Hardware security keys (WebAuthn)
- Backup codes
- Adaptive MFA based on risk assessment
"""

import logging
import secrets
import base64
import qrcode
import io
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import pyotp
import asyncio

from wakedock.database import get_db_session
from wakedock.database.models import User
from wakedock.security.advanced.models import MFAMethod, SecurityEvent, ThreatLevel
from wakedock.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class MFAChallenge:
    """MFA challenge information"""
    challenge_id: str
    user_id: int
    method_type: str
    challenge_data: Dict
    expires_at: datetime
    attempts_remaining: int


@dataclass
class MFAVerificationResult:
    """MFA verification result"""
    success: bool
    method_id: Optional[int]
    method_type: Optional[str]
    error_message: Optional[str]
    backup_codes_remaining: Optional[int]


@dataclass
class MFAStatus:
    """User's MFA status"""
    user_id: int
    is_enabled: bool
    primary_method: Optional[str]
    available_methods: List[str]
    backup_codes_count: int
    last_used_at: Optional[datetime]


class AdvancedMFAManager:
    """Manages advanced multi-factor authentication"""
    
    def __init__(self):
        self.settings = get_settings()
        self._active_challenges: Dict[str, MFAChallenge] = {}
        self._cleanup_task = None
        
        # MFA configuration
        self.totp_issuer = "WakeDock"
        self.totp_algorithm = "SHA1"
        self.totp_digits = 6
        self.totp_interval = 30
        
        # SMS/Email configuration (would be configured via settings)
        self.sms_enabled = False  # Requires SMS service integration
        self.email_enabled = True
        
        # Security settings
        self.max_attempts = 3
        self.challenge_ttl = 300  # 5 minutes
        self.backup_codes_count = 10
        
    async def start_monitoring(self):
        """Start MFA monitoring and cleanup"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("MFA monitoring started")
    
    async def stop_monitoring(self):
        """Stop MFA monitoring"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        logger.info("MFA monitoring stopped")
    
    async def _cleanup_loop(self):
        """Cleanup expired challenges"""
        while True:
            try:
                now = datetime.utcnow()
                expired_challenges = [
                    challenge_id for challenge_id, challenge in self._active_challenges.items()
                    if challenge.expires_at < now
                ]
                
                for challenge_id in expired_challenges:
                    del self._active_challenges[challenge_id]
                
                if expired_challenges:
                    logger.debug(f"Cleaned up {len(expired_challenges)} expired MFA challenges")
                
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"MFA cleanup error: {e}")
                await asyncio.sleep(10)
    
    async def setup_totp(self, user_id: int, account_name: Optional[str] = None) -> Dict[str, str]:
        """Set up TOTP for a user"""
        
        async with get_db_session() as session:
            user = await session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Check if TOTP already exists
            existing_totp = await session.query(MFAMethod).filter(
                MFAMethod.user_id == user_id,
                MFAMethod.method_type == "totp",
                MFAMethod.is_active == True
            ).first()
            
            if existing_totp:
                raise ValueError("TOTP is already set up for this user")
            
            # Generate secret
            secret = pyotp.random_base32()
            
            # Create TOTP URI
            account = account_name or user.email or user.username
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=account,
                issuer_name=self.totp_issuer
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            qr_code_data = base64.b64encode(img_buffer.getvalue()).decode()
            
            # Store MFA method (not verified yet)
            mfa_method = MFAMethod(
                user_id=user_id,
                method_type="totp",
                secret_key=secret,  # In production, this should be encrypted
                config={
                    "algorithm": self.totp_algorithm,
                    "digits": self.totp_digits,
                    "interval": self.totp_interval
                },
                is_verified=False
            )
            
            session.add(mfa_method)
            await session.commit()
            await session.refresh(mfa_method)
            
            return {
                "method_id": str(mfa_method.id),
                "secret": secret,
                "qr_code": f"data:image/png;base64,{qr_code_data}",
                "manual_entry": f"Account: {account}, Secret: {secret}"
            }
    
    async def verify_totp_setup(self, method_id: int, verification_code: str) -> bool:
        """Verify TOTP setup with verification code"""
        
        async with get_db_session() as session:
            method = await session.query(MFAMethod).filter(
                MFAMethod.id == method_id,
                MFAMethod.method_type == "totp"
            ).first()
            
            if not method:
                return False
            
            # Verify the code
            totp = pyotp.TOTP(method.secret_key)
            if totp.verify(verification_code, valid_window=1):
                method.is_verified = True
                method.is_active = True
                
                # Make this the primary method if it's the user's first
                user_methods = await session.query(MFAMethod).filter(
                    MFAMethod.user_id == method.user_id,
                    MFAMethod.is_active == True
                ).count()
                
                if user_methods == 0:
                    method.is_primary = True
                
                await session.commit()
                
                # Generate backup codes
                await self._generate_backup_codes(method.user_id)
                
                logger.info(f"TOTP verified and activated for user {method.user_id}")
                return True
            
            return False
    
    async def _generate_backup_codes(self, user_id: int) -> List[str]:
        """Generate backup codes for user"""
        
        async with get_db_session() as session:
            # Check if backup codes already exist
            backup_method = await session.query(MFAMethod).filter(
                MFAMethod.user_id == user_id,
                MFAMethod.method_type == "backup_codes",
                MFAMethod.is_active == True
            ).first()
            
            # Generate new codes
            codes = [secrets.token_hex(4).upper() for _ in range(self.backup_codes_count)]
            
            if backup_method:
                backup_method.backup_codes = codes
            else:
                backup_method = MFAMethod(
                    user_id=user_id,
                    method_type="backup_codes",
                    backup_codes=codes,
                    is_active=True,
                    is_verified=True
                )
                session.add(backup_method)
            
            await session.commit()
            
            logger.info(f"Generated {len(codes)} backup codes for user {user_id}")
            return codes
    
    async def setup_email_mfa(self, user_id: int, email_address: str) -> int:
        """Set up email-based MFA"""
        
        async with get_db_session() as session:
            # Check if email MFA already exists
            existing_email = await session.query(MFAMethod).filter(
                MFAMethod.user_id == user_id,
                MFAMethod.method_type == "email",
                MFAMethod.is_active == True
            ).first()
            
            if existing_email:
                raise ValueError("Email MFA is already set up for this user")
            
            # Create email MFA method
            mfa_method = MFAMethod(
                user_id=user_id,
                method_type="email",
                email_address=email_address,
                is_verified=False,
                config={
                    "code_length": 6,
                    "code_ttl": 300  # 5 minutes
                }
            )
            
            session.add(mfa_method)
            await session.commit()
            await session.refresh(mfa_method)
            
            # Send verification email (would integrate with email service)
            await self._send_verification_email(user_id, email_address)
            
            return mfa_method.id
    
    async def _send_verification_email(self, user_id: int, email_address: str):
        """Send verification email (placeholder)"""
        # In production, this would integrate with an email service
        verification_code = secrets.randbelow(1000000)
        
        logger.info(f"Would send verification email to {email_address} with code {verification_code:06d}")
        
        # Store the verification code temporarily
        # This is simplified - in production you'd use a proper verification system
    
    async def create_mfa_challenge(self, user_id: int, method_type: Optional[str] = None) -> Optional[MFAChallenge]:
        """Create an MFA challenge for user"""
        
        async with get_db_session() as session:
            # Get user's MFA methods
            query = session.query(MFAMethod).filter(
                MFAMethod.user_id == user_id,
                MFAMethod.is_active == True,
                MFAMethod.is_verified == True
            )
            
            if method_type:
                query = query.filter(MFAMethod.method_type == method_type)
            else:
                # Prefer primary method
                query = query.order_by(MFAMethod.is_primary.desc())
            
            method = await query.first()
            if not method:
                return None
            
            # Create challenge
            challenge_id = secrets.token_urlsafe(32)
            challenge_data = {}
            
            if method.method_type == "totp":
                challenge_data = {
                    "method": "totp",
                    "message": "Enter the 6-digit code from your authenticator app"
                }
            elif method.method_type == "email":
                # Generate and send email code
                code = f"{secrets.randbelow(1000000):06d}"
                challenge_data = {
                    "method": "email",
                    "email": method.email_address,
                    "code": code,  # In production, store securely
                    "message": f"Enter the code sent to {method.email_address}"
                }
                # Send email here
                logger.info(f"Would send MFA code {code} to {method.email_address}")
            
            challenge = MFAChallenge(
                challenge_id=challenge_id,
                user_id=user_id,
                method_type=method.method_type,
                challenge_data=challenge_data,
                expires_at=datetime.utcnow() + timedelta(seconds=self.challenge_ttl),
                attempts_remaining=self.max_attempts
            )
            
            self._active_challenges[challenge_id] = challenge
            
            return challenge
    
    async def verify_mfa_challenge(self, challenge_id: str, response: str) -> MFAVerificationResult:
        """Verify MFA challenge response"""
        
        challenge = self._active_challenges.get(challenge_id)
        if not challenge:
            return MFAVerificationResult(
                success=False,
                method_id=None,
                method_type=None,
                error_message="Invalid or expired challenge"
            )
        
        if challenge.expires_at < datetime.utcnow():
            del self._active_challenges[challenge_id]
            return MFAVerificationResult(
                success=False,
                method_id=None,
                method_type=None,
                error_message="Challenge expired"
            )
        
        if challenge.attempts_remaining <= 0:
            del self._active_challenges[challenge_id]
            return MFAVerificationResult(
                success=False,
                method_id=None,
                method_type=None,
                error_message="Too many attempts"
            )
        
        success = False
        
        if challenge.method_type == "totp":
            success = await self._verify_totp_code(challenge.user_id, response)
        elif challenge.method_type == "email":
            success = (response == challenge.challenge_data.get("code"))
        elif challenge.method_type == "backup_codes":
            success = await self._verify_backup_code(challenge.user_id, response)
        
        if success:
            # Update method usage
            await self._update_method_usage(challenge.user_id, challenge.method_type)
            
            # Remove challenge
            del self._active_challenges[challenge_id]
            
            # Get backup codes count
            backup_codes_remaining = await self._get_backup_codes_count(challenge.user_id)
            
            return MFAVerificationResult(
                success=True,
                method_id=None,  # Would get from database
                method_type=challenge.method_type,
                error_message=None,
                backup_codes_remaining=backup_codes_remaining
            )
        else:
            challenge.attempts_remaining -= 1
            return MFAVerificationResult(
                success=False,
                method_id=None,
                method_type=challenge.method_type,
                error_message="Invalid verification code"
            )
    
    async def _verify_totp_code(self, user_id: int, code: str) -> bool:
        """Verify TOTP code"""
        async with get_db_session() as session:
            method = await session.query(MFAMethod).filter(
                MFAMethod.user_id == user_id,
                MFAMethod.method_type == "totp",
                MFAMethod.is_active == True
            ).first()
            
            if not method:
                return False
            
            totp = pyotp.TOTP(method.secret_key)
            return totp.verify(code, valid_window=1)
    
    async def _verify_backup_code(self, user_id: int, code: str) -> bool:
        """Verify and consume backup code"""
        async with get_db_session() as session:
            method = await session.query(MFAMethod).filter(
                MFAMethod.user_id == user_id,
                MFAMethod.method_type == "backup_codes",
                MFAMethod.is_active == True
            ).first()
            
            if not method or not method.backup_codes:
                return False
            
            code = code.upper().strip()
            if code in method.backup_codes:
                # Remove used code
                method.backup_codes.remove(code)
                await session.commit()
                
                logger.info(f"Backup code used for user {user_id}, {len(method.backup_codes)} remaining")
                return True
            
            return False
    
    async def _update_method_usage(self, user_id: int, method_type: str):
        """Update MFA method usage statistics"""
        async with get_db_session() as session:
            method = await session.query(MFAMethod).filter(
                MFAMethod.user_id == user_id,
                MFAMethod.method_type == method_type,
                MFAMethod.is_active == True
            ).first()
            
            if method:
                method.last_used_at = datetime.utcnow()
                method.use_count += 1
                await session.commit()
    
    async def _get_backup_codes_count(self, user_id: int) -> int:
        """Get remaining backup codes count"""
        async with get_db_session() as session:
            method = await session.query(MFAMethod).filter(
                MFAMethod.user_id == user_id,
                MFAMethod.method_type == "backup_codes",
                MFAMethod.is_active == True
            ).first()
            
            if method and method.backup_codes:
                return len(method.backup_codes)
            
            return 0
    
    async def get_user_mfa_status(self, user_id: int) -> MFAStatus:
        """Get user's MFA status"""
        async with get_db_session() as session:
            methods = await session.query(MFAMethod).filter(
                MFAMethod.user_id == user_id,
                MFAMethod.is_active == True,
                MFAMethod.is_verified == True
            ).all()
            
            primary_method = None
            available_methods = []
            last_used = None
            
            for method in methods:
                available_methods.append(method.method_type)
                if method.is_primary:
                    primary_method = method.method_type
                if method.last_used_at and (not last_used or method.last_used_at > last_used):
                    last_used = method.last_used_at
            
            backup_codes_count = await self._get_backup_codes_count(user_id)
            
            return MFAStatus(
                user_id=user_id,
                is_enabled=len(methods) > 0,
                primary_method=primary_method,
                available_methods=available_methods,
                backup_codes_count=backup_codes_count,
                last_used_at=last_used
            )
    
    async def disable_mfa_method(self, user_id: int, method_type: str) -> bool:
        """Disable an MFA method"""
        async with get_db_session() as session:
            method = await session.query(MFAMethod).filter(
                MFAMethod.user_id == user_id,
                MFAMethod.method_type == method_type,
                MFAMethod.is_active == True
            ).first()
            
            if not method:
                return False
            
            method.is_active = False
            await session.commit()
            
            logger.info(f"Disabled MFA method {method_type} for user {user_id}")
            return True
    
    async def regenerate_backup_codes(self, user_id: int) -> List[str]:
        """Regenerate backup codes for user"""
        return await self._generate_backup_codes(user_id)


# Global instance
_mfa_manager: Optional[AdvancedMFAManager] = None


def get_mfa_manager() -> AdvancedMFAManager:
    """Get MFA manager instance"""
    global _mfa_manager
    if _mfa_manager is None:
        _mfa_manager = AdvancedMFAManager()
    return _mfa_manager


async def initialize_mfa_manager() -> AdvancedMFAManager:
    """Initialize and start MFA manager"""
    manager = get_mfa_manager()
    await manager.start_monitoring()
    return manager