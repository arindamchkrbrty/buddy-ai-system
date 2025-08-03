import re
import logging
import hashlib
import jwt
import secrets
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class UserRole(Enum):
    MASTER = "master"
    STANDARD = "standard"
    UNKNOWN = "unknown"

@dataclass
class AuthResult:
    authenticated: bool
    user_id: str
    role: UserRole
    method: str
    device_id: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class AuthenticationManager:
    """Manages iPhone device authentication and voice passphrase system."""
    
    def __init__(self):
        self.master_user = "Arindam"
        self.master_passphrase = "happy birthday"
        self.passphrase_pattern = re.compile(
            r"happy\s+birthday",
            re.IGNORECASE
        )
        
        # JWT Configuration
        self.jwt_secret = secrets.token_hex(32)  # Generate secure secret
        self.token_expiry_hours = 24
        
        # Active sessions
        self.active_sessions: Dict[str, Dict] = {}  # token -> session_info
        
        # Master device whitelist (iPhone device IDs)
        self.master_devices = {
            # Example iPhone device identifiers - these would be actual device IDs
            "iPhone14,7",  # iPhone 13 mini
            "iPhone14,2",  # iPhone 13
            "iPhone14,3",  # iPhone 13 Pro
            "iPhone15,2",  # iPhone 14
            "iPhone15,3",  # iPhone 14 Plus
            "iPhone16,1",  # iPhone 15
            "iPhone16,2",  # iPhone 15 Plus
        }
        
        # Session tracking
        self.authenticated_sessions: Dict[str, AuthResult] = {}
        self.authentication_log: List[Dict] = []
        
        # Device fingerprinting headers to check
        self.device_headers = [
            "user-agent",
            "x-device-id", 
            "x-device-uuid",
            "x-unique-id",
            "device-id",
            "cf-connecting-ip"
        ]
    
    def authenticate_request(self, headers: Dict[str, str], message: str = "", user_id: str = "default") -> AuthResult:
        """Main authentication method that checks tokens, passphrase, and device."""
        
        # First check for existing JWT token
        token_auth = self._check_jwt_token(headers)
        if token_auth.authenticated:
            self._log_authentication_attempt(token_auth, headers, message)
            return token_auth
        
        # Then check for voice passphrase in message
        passphrase_auth = self._check_voice_passphrase(message, user_id)
        if passphrase_auth.authenticated:
            self._log_authentication_attempt(passphrase_auth, headers, message)
            return passphrase_auth
        
        # Then check device authentication
        device_auth = self._check_device_authentication(headers, user_id)
        if device_auth.authenticated:
            self._log_authentication_attempt(device_auth, headers, message)
            return device_auth
        
        # Default to unknown user
        auth_result = AuthResult(
            authenticated=False,
            user_id=user_id,
            role=UserRole.UNKNOWN,
            method="none"
        )
        
        self._log_authentication_attempt(auth_result, headers, message)
        return auth_result
    
    def _check_voice_passphrase(self, message: str, user_id: str) -> AuthResult:
        """Check if message contains the master voice passphrase."""
        if not message:
            return AuthResult(False, user_id, UserRole.UNKNOWN, "none")
        
        # Check for 'Happy birthday' passphrase anywhere in message
        if "happy birthday" in message.lower():
            logger.info(f"🎉 Cinematic authentication successful for {self.master_user}")
            return AuthResult(
                authenticated=True,
                user_id=self.master_user,
                role=UserRole.MASTER,
                method="cinematic_passphrase"
            )
        
        return AuthResult(False, user_id, UserRole.UNKNOWN, "none")
    
    def _check_device_authentication(self, headers: Dict[str, str], user_id: str) -> AuthResult:
        """Check if request comes from a whitelisted iPhone device."""
        
        # Extract device information from headers
        device_info = self._extract_device_info(headers)
        
        # Check User-Agent for iPhone identification
        user_agent = headers.get("user-agent", "").lower()
        if "iphone" in user_agent:
            # Try to extract iOS version and device model
            device_model = self._extract_iphone_model(user_agent)
            
            # Check if it's from a master device
            if device_model and any(device in device_model for device in self.master_devices):
                logger.info(f"iPhone device authentication successful: {device_model}")
                return AuthResult(
                    authenticated=True,
                    user_id=self.master_user,
                    role=UserRole.MASTER,
                    method="device_iphone",
                    device_id=device_model
                )
            
            # Check for custom device ID headers
            for header in self.device_headers:
                device_id = headers.get(header, "")
                if device_id and device_id in self.master_devices:
                    logger.info(f"Device ID authentication successful: {device_id}")
                    return AuthResult(
                        authenticated=True,
                        user_id=self.master_user,
                        role=UserRole.MASTER,
                        method="device_id",
                        device_id=device_id
                    )
            
            # iPhone but not whitelisted - standard user
            return AuthResult(
                authenticated=True,
                user_id=user_id or "iphone_user",
                role=UserRole.STANDARD,
                method="device_iphone_unverified",
                device_id=device_model
            )
        
        return AuthResult(False, user_id, UserRole.UNKNOWN, "none")
    
    def _extract_device_info(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Extract device information from request headers."""
        device_info = {}
        
        for header in self.device_headers:
            value = headers.get(header, "")
            if value:
                device_info[header] = value
        
        return device_info
    
    def _extract_iphone_model(self, user_agent: str) -> Optional[str]:
        """Extract iPhone model from User-Agent string."""
        # Look for iPhone model patterns
        iphone_pattern = re.compile(r"iPhone(\d+,\d+)", re.IGNORECASE)
        match = iphone_pattern.search(user_agent)
        
        if match:
            return f"iPhone{match.group(1)}"
        
        # Fallback to generic iPhone identification
        if "iphone" in user_agent.lower():
            return "iPhone_Generic"
        
        return None
    
    def _log_authentication_attempt(self, auth_result: AuthResult, headers: Dict[str, str], message: str):
        """Log authentication attempts for security monitoring."""
        log_entry = {
            "timestamp": auth_result.timestamp,
            "authenticated": auth_result.authenticated,
            "user_id": auth_result.user_id,
            "role": auth_result.role.value,
            "method": auth_result.method,
            "device_id": auth_result.device_id,
            "user_agent": headers.get("user-agent", ""),
            "ip_address": headers.get("cf-connecting-ip", headers.get("x-forwarded-for", "unknown")),
            "message_length": len(message) if message else 0,
            "has_passphrase": "authenticate" in message.lower() if message else False
        }
        
        self.authentication_log.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.authentication_log) > 1000:
            self.authentication_log = self.authentication_log[-1000:]
        
        # Log security events
        if auth_result.authenticated:
            logger.info(f"Authentication successful: {auth_result.user_id} via {auth_result.method}")
        else:
            logger.warning(f"Authentication failed for user: {auth_result.user_id}")
    
    def is_master_user(self, auth_result: AuthResult) -> bool:
        """Check if authenticated user is the master user."""
        return auth_result.authenticated and auth_result.role == UserRole.MASTER
    
    def get_user_capabilities(self, auth_result: AuthResult) -> List[str]:
        """Get user capabilities based on authentication level."""
        if not auth_result.authenticated:
            return ["limited_responses"]
        
        if auth_result.role == UserRole.MASTER:
            return [
                "full_access",
                "admin_commands", 
                "override_conversations",
                "access_all_histories",
                "set_user_policies",
                "view_security_logs",
                "manage_whitelist"
            ]
        elif auth_result.role == UserRole.STANDARD:
            return [
                "standard_chat",
                "personal_history",
                "basic_commands"
            ]
        else:
            return ["limited_responses", "basic_info"]
    
    def add_master_device(self, device_id: str) -> bool:
        """Add a device to the master whitelist."""
        if device_id and device_id not in self.master_devices:
            self.master_devices.add(device_id)
            logger.info(f"Added device to master whitelist: {device_id}")
            return True
        return False
    
    def remove_master_device(self, device_id: str) -> bool:
        """Remove a device from the master whitelist."""
        if device_id in self.master_devices:
            self.master_devices.remove(device_id)
            logger.info(f"Removed device from master whitelist: {device_id}")
            return True
        return False
    
    def get_security_status(self) -> Dict:
        """Get current security status and statistics."""
        recent_attempts = [log for log in self.authentication_log[-100:]]
        successful_auths = [log for log in recent_attempts if log["authenticated"]]
        failed_auths = [log for log in recent_attempts if not log["authenticated"]]
        
        return {
            "master_devices_count": len(self.master_devices),
            "recent_attempts": len(recent_attempts),
            "successful_authentications": len(successful_auths),
            "failed_authentications": len(failed_auths),
            "master_authentications": len([auth for auth in successful_auths if auth["role"] == "master"]),
            "last_master_auth": max([auth["timestamp"] for auth in successful_auths if auth["role"] == "master"], default="never"),
            "authentication_methods": list(set([auth["method"] for auth in successful_auths]))
        }
    
    def get_authentication_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent authentication logs."""
        return self.authentication_log[-limit:] if limit > 0 else self.authentication_log
    
    def _check_jwt_token(self, headers: Dict[str, str]) -> AuthResult:
        """Check for valid JWT token in Authorization header."""
        auth_header = headers.get("authorization", "")
        
        if not auth_header.startswith("Bearer "):
            return AuthResult(False, "default", UserRole.UNKNOWN, "none")
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            # Decode and verify JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            
            # Check if token is still active
            if token in self.active_sessions:
                session_info = self.active_sessions[token]
                
                logger.info(f"🔐 JWT token authentication successful for {payload['user_id']}")
                return AuthResult(
                    authenticated=True,
                    user_id=payload["user_id"],
                    role=UserRole.MASTER,
                    method="jwt_token",
                    device_id=session_info.get("device_id")
                )
        
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            # Clean up expired token
            if token in self.active_sessions:
                del self.active_sessions[token]
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
        
        return AuthResult(False, "default", UserRole.UNKNOWN, "none")
    
    def generate_session_token(self, auth_result: AuthResult) -> str:
        """Generate a JWT session token for authenticated master user."""
        if not auth_result.authenticated or auth_result.role != UserRole.MASTER:
            raise ValueError("Only authenticated master users can get session tokens")
        
        # Create JWT payload
        payload = {
            "user_id": auth_result.user_id,
            "role": auth_result.role.value,
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=self.token_expiry_hours)).isoformat()
        }
        
        # Generate token
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        
        # Store session info
        self.active_sessions[token] = {
            "user_id": auth_result.user_id,
            "role": auth_result.role.value,
            "device_id": auth_result.device_id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": payload["expires_at"],
            "auth_method": auth_result.method
        }
        
        logger.info(f"🎟️ Generated 24-hour session token for {auth_result.user_id}")
        return token
    
    def revoke_session_token(self, token: str) -> bool:
        """Revoke a session token."""
        if token in self.active_sessions:
            del self.active_sessions[token]
            logger.info("🚫 Session token revoked")
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired session tokens."""
        current_time = datetime.utcnow()
        expired_tokens = []
        
        for token, session_info in self.active_sessions.items():
            expires_at = datetime.fromisoformat(session_info["expires_at"])
            if current_time > expires_at:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.active_sessions[token]
        
        if expired_tokens:
            logger.info(f"🧹 Cleaned up {len(expired_tokens)} expired session tokens")