"""
Multi-Factor Authentication (MFA) Manager
Implements TOTP-based 2FA with backup codes and security features
"""

import pyotp
import qrcode
from io import BytesIO
import base64
import secrets
import string
import logging
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class MFASetup:
    """MFA setup data"""
    secret: str
    qr_code: str
    backup_codes: List[str]
    
@dataclass
class MFAVerification:
    """MFA verification result"""
    success: bool
    method: str  # 'totp' or 'backup_code'
    remaining_codes: Optional[int] = None
    error: Optional[str] = None

class MFAManager:
    """Multi-Factor Authentication Manager"""
    
    def __init__(self, app_name: str = "WakeDock", issuer: str = "WakeDock Platform"):
        self.app_name = app_name
        self.issuer = issuer
        self.backup_codes_count = 8
        self.totp_window = 1  # ±30 seconds tolerance
        
    def generate_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def generate_setup(self, user_email: str) -> MFASetup:
        """Generate complete MFA setup for user"""
        secret = self.generate_secret()
        qr_code = self._generate_qr_code(user_email, secret)
        backup_codes = self._generate_backup_codes()
        
        return MFASetup(
            secret=secret,
            qr_code=qr_code,
            backup_codes=backup_codes
        )
    
    def _generate_qr_code(self, user_email: str, secret: str) -> str:
        """Generate QR code for authenticator app setup"""
        try:
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=user_email,
                issuer_name=self.issuer
            )
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            # Convert to base64 image
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_b64 = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_b64}"
            
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            raise
    
    def _generate_backup_codes(self) -> List[str]:
        """Generate backup recovery codes"""
        codes = []
        for _ in range(self.backup_codes_count):
            # Generate 8-character code
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) 
                          for _ in range(8))
            # Format as XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        
        return codes
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=self.totp_window)
        except Exception as e:
            logger.error(f"TOTP verification failed: {e}")
            return False
    
    def verify_backup_code(self, used_codes: List[str], provided_code: str) -> bool:
        """Verify backup code (case-insensitive)"""
        normalized_code = provided_code.upper().strip()
        return normalized_code not in used_codes
    
    def verify_mfa(
        self, 
        secret: str, 
        token: str, 
        backup_codes: List[str],
        used_backup_codes: List[str]
    ) -> MFAVerification:
        """Verify MFA token (TOTP or backup code)"""
        
        # Remove spaces and convert to uppercase
        clean_token = token.replace(" ", "").replace("-", "").upper()
        
        # Try TOTP first
        if len(clean_token) == 6 and clean_token.isdigit():
            if self.verify_totp(secret, clean_token):
                return MFAVerification(
                    success=True,
                    method="totp"
                )
        
        # Try backup code
        if len(clean_token) == 8 and clean_token.isalnum():
            # Format as XXXX-XXXX for comparison
            formatted_code = f"{clean_token[:4]}-{clean_token[4:]}"
            
            if formatted_code in backup_codes and formatted_code not in used_backup_codes:
                remaining_codes = len(backup_codes) - len(used_backup_codes) - 1
                return MFAVerification(
                    success=True,
                    method="backup_code",
                    remaining_codes=remaining_codes
                )
        
        return MFAVerification(
            success=False,
            method="unknown",
            error="Invalid token or code"
        )
    
    def generate_recovery_codes(self) -> List[str]:
        """Generate new recovery codes (for when user runs out)"""
        return self._generate_backup_codes()
    
    def get_current_totp(self, secret: str) -> str:
        """Get current TOTP code (for testing)"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.now()
        except Exception as e:
            logger.error(f"Failed to get current TOTP: {e}")
            return ""
    
    def validate_secret(self, secret: str) -> bool:
        """Validate TOTP secret format"""
        try:
            pyotp.TOTP(secret)
            return True
        except Exception:
            return False

class MFAService:
    """MFA Service with database integration"""
    
    def __init__(self, db, cache_service, mfa_manager: MFAManager):
        self.db = db
        self.cache = cache_service
        self.mfa = mfa_manager
        
    async def setup_mfa(self, user_id: str, user_email: str) -> MFASetup:
        """Setup MFA for user"""
        try:
            # Generate MFA setup
            setup = self.mfa.generate_setup(user_email)
            
            # Store in cache temporarily (10 minutes)
            cache_key = f"mfa_setup:{user_id}"
            await self.cache.set(cache_key, {
                "secret": setup.secret,
                "backup_codes": setup.backup_codes,
                "timestamp": datetime.utcnow().isoformat()
            }, ttl=600)
            
            logger.info(f"MFA setup generated for user {user_id}")
            return setup
            
        except Exception as e:
            logger.error(f"Failed to setup MFA for user {user_id}: {e}")
            raise
    
    async def confirm_mfa_setup(
        self, 
        user_id: str, 
        verification_code: str
    ) -> Tuple[bool, Optional[str]]:
        """Confirm MFA setup with verification code"""
        try:
            # Get setup from cache
            cache_key = f"mfa_setup:{user_id}"
            setup_data = await self.cache.get(cache_key)
            
            if not setup_data:
                return False, "MFA setup expired or not found"
            
            # Verify code
            if not self.mfa.verify_totp(setup_data["secret"], verification_code):
                return False, "Invalid verification code"
            
            # Save to database
            await self._save_mfa_config(user_id, setup_data)
            
            # Clear cache
            await self.cache.delete(cache_key)
            
            logger.info(f"MFA setup confirmed for user {user_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Failed to confirm MFA setup for user {user_id}: {e}")
            return False, str(e)
    
    async def verify_mfa_token(
        self, 
        user_id: str, 
        token: str
    ) -> MFAVerification:
        """Verify MFA token for user"""
        try:
            # Get user MFA config
            mfa_config = await self._get_mfa_config(user_id)
            if not mfa_config:
                return MFAVerification(
                    success=False,
                    method="unknown",
                    error="MFA not configured"
                )
            
            # Verify token
            result = self.mfa.verify_mfa(
                secret=mfa_config["secret"],
                token=token,
                backup_codes=mfa_config["backup_codes"],
                used_backup_codes=mfa_config["used_backup_codes"]
            )
            
            # If backup code used, mark as used
            if result.success and result.method == "backup_code":
                await self._mark_backup_code_used(user_id, token)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to verify MFA token for user {user_id}: {e}")
            return MFAVerification(
                success=False,
                method="unknown",
                error=str(e)
            )
    
    async def disable_mfa(self, user_id: str) -> bool:
        """Disable MFA for user"""
        try:
            # Remove from database
            await self._remove_mfa_config(user_id)
            
            # Clear any cached setup
            cache_key = f"mfa_setup:{user_id}"
            await self.cache.delete(cache_key)
            
            logger.info(f"MFA disabled for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable MFA for user {user_id}: {e}")
            return False
    
    async def regenerate_backup_codes(self, user_id: str) -> List[str]:
        """Regenerate backup codes for user"""
        try:
            new_codes = self.mfa.generate_recovery_codes()
            
            # Update in database
            await self._update_backup_codes(user_id, new_codes)
            
            logger.info(f"Backup codes regenerated for user {user_id}")
            return new_codes
            
        except Exception as e:
            logger.error(f"Failed to regenerate backup codes for user {user_id}: {e}")
            raise
    
    async def _save_mfa_config(self, user_id: str, setup_data: dict) -> None:
        """Save MFA configuration to database"""
        # Implementation depends on your database schema
        # This is a placeholder for the actual database operations
        pass
    
    async def _get_mfa_config(self, user_id: str) -> Optional[dict]:
        """Get MFA configuration from database"""
        # Implementation depends on your database schema
        # This is a placeholder for the actual database operations
        return None
    
    async def _mark_backup_code_used(self, user_id: str, code: str) -> None:
        """Mark backup code as used"""
        # Implementation depends on your database schema
        pass
    
    async def _remove_mfa_config(self, user_id: str) -> None:
        """Remove MFA configuration from database"""
        # Implementation depends on your database schema
        pass
    
    async def _update_backup_codes(self, user_id: str, new_codes: List[str]) -> None:
        """Update backup codes in database"""
        # Implementation depends on your database schema
        pass
