import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .authentication import AuthResult, UserRole, AuthenticationManager

logger = logging.getLogger(__name__)

class AccessController:
    """Manages user access control and capabilities based on authentication."""
    
    def __init__(self, auth_manager: AuthenticationManager):
        self.auth_manager = auth_manager
        self.user_policies: Dict[str, Dict] = {}
        self.conversation_overrides: Dict[str, str] = {}  # user_id -> master_user_id
        
    def check_message_access(self, auth_result: AuthResult, message: str) -> Dict[str, Any]:
        """Check if user can send this message and determine response level."""
        
        access_info = {
            "allowed": True,
            "response_level": "full",
            "restrictions": [],
            "capabilities": self.auth_manager.get_user_capabilities(auth_result)
        }
        
        if not auth_result.authenticated:
            # Check if user is asking for admin commands - trigger cinematic auth flow
            if self._is_admin_command(message):
                access_info.update({
                    "allowed": False,
                    "response_level": "auth_required",
                    "restrictions": ["admin_command_denied"],
                    "cinematic_response": self._get_cinematic_auth_prompt()
                })
            else:
                access_info.update({
                    "allowed": True,  # Allow but with restrictions
                    "response_level": "limited",
                    "restrictions": ["limited_responses", "no_history", "basic_info_only"],
                    "cinematic_response": "I can help with basic questions, but for full capabilities, I need authentication first."
                })
            return access_info
        
        if auth_result.role == UserRole.MASTER:
            access_info.update({
                "response_level": "master",
                "admin_access": True,
                "can_override": True
            })
        elif auth_result.role == UserRole.STANDARD:
            access_info.update({
                "response_level": "standard",
                "admin_access": False,
                "can_override": False
            })
        
        # Check for admin commands
        if self._is_admin_command(message):
            if auth_result.role != UserRole.MASTER:
                access_info.update({
                    "allowed": False,
                    "restrictions": ["admin_command_denied"],
                    "cinematic_response": self._get_cinematic_auth_prompt()
                })
        
        return access_info
    
    def _get_cinematic_auth_prompt(self) -> str:
        """Get cinematic authentication prompt."""
        import random
        
        prompts = [
            "🤖 I recognize your voice pattern, but I need to verify your identity. What's the phrase that started our journey together?",
            "🔐 Access to my core systems requires the special phrase. You know the one.",
            "🎭 I detect familiar patterns, but security protocols require authentication. Please provide the passphrase.",
            "⚡ My advanced capabilities are locked. Speak the words that unlock my full potential."
        ]
        
        return random.choice(prompts)
    
    def _is_admin_command(self, message: str) -> bool:
        """Check if message contains admin commands."""
        admin_patterns = [
            "admin", "status", "logs", "users", "override", 
            "security", "whitelist", "config", "reset"
        ]
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in admin_patterns)
    
    def process_admin_command(self, auth_result: AuthResult, message: str) -> Optional[str]:
        """Process admin commands for master user."""
        if auth_result.role != UserRole.MASTER:
            return "❌ Access denied. Admin commands require master authentication."
        
        message_lower = message.lower().strip()
        
        # Status command
        if "status" in message_lower:
            return self._get_system_status()
        
        # Security logs
        if "logs" in message_lower or "security" in message_lower:
            return self._get_security_logs()
        
        # User list
        if "users" in message_lower:
            return self._get_user_list()
        
        # Whitelist management
        if "whitelist" in message_lower:
            return self._manage_whitelist(message_lower)
        
        # System reset
        if "reset" in message_lower:
            return self._reset_system()
        
        return None
    
    def _get_system_status(self) -> str:
        """Get system status for admin."""
        status = self.auth_manager.get_security_status()
        
        return f"""🔐 **BUDDY SECURITY STATUS**

**Authentication:**
• Master Devices: {status['master_devices_count']} whitelisted
• Recent Attempts: {status['recent_attempts']} 
• Successful: {status['successful_authentications']}
• Failed: {status['failed_authentications']}
• Master Auths: {status['master_authentications']}

**Last Master Auth:** {status['last_master_auth']}
**Auth Methods:** {', '.join(status['authentication_methods']) if status['authentication_methods'] else 'None'}

**System:**
• Status: Online ✅
• Security Level: High 🔒
• Access Control: Active"""
    
    def _get_security_logs(self) -> str:
        """Get recent security logs."""
        logs = self.auth_manager.get_authentication_logs(10)
        
        if not logs:
            return "📋 No recent authentication logs."
        
        log_text = "🔍 **RECENT SECURITY LOGS:**\n\n"
        
        for log in reversed(logs[-10:]):  # Show most recent first
            status = "✅" if log['authenticated'] else "❌"
            timestamp = log['timestamp'].split('T')[1][:8]  # Just time part
            
            log_text += f"{status} {timestamp} | {log['user_id']} | {log['method']} | {log['role']}\n"
        
        return log_text
    
    def _get_user_list(self) -> str:
        """Get list of recent users."""
        logs = self.auth_manager.get_authentication_logs(100)
        users = set()
        
        for log in logs:
            if log['authenticated']:
                users.add(f"{log['user_id']} ({log['role']})")
        
        if not users:
            return "👥 No authenticated users in recent logs."
        
        return f"👥 **RECENT USERS:**\n\n" + "\n".join(f"• {user}" for user in sorted(users))
    
    def _manage_whitelist(self, message: str) -> str:
        """Manage device whitelist."""
        if "add" in message:
            return "⚠️ Use device headers or contact admin to add devices to whitelist."
        elif "remove" in message:
            return "⚠️ Use admin interface to remove devices from whitelist."
        elif "list" in message:
            devices = list(self.auth_manager.master_devices)
            return f"📱 **WHITELISTED DEVICES:**\n\n" + "\n".join(f"• {device}" for device in devices)
        else:
            return "📱 Whitelist commands: 'list', 'add [device]', 'remove [device]'"
    
    def _reset_system(self) -> str:
        """Reset system (limited reset for security)."""
        # Only clear logs, not devices or core security
        old_count = len(self.auth_manager.authentication_log)
        self.auth_manager.authentication_log = []
        
        return f"🔄 **SYSTEM RESET COMPLETE**\n\nCleared {old_count} authentication logs.\nDevice whitelist and core security maintained."
    
    def get_response_prefix(self, auth_result: AuthResult) -> str:
        """Get cinematic response prefix showing authentication status."""
        
        if not auth_result.authenticated:
            return ""
        
        if auth_result.role == UserRole.MASTER:
            # Get time of day for greeting
            current_hour = datetime.now().hour
            if current_hour < 12:
                greeting = "morning"
            elif current_hour < 17:
                greeting = "afternoon"
            else:
                greeting = "evening"
            
            if auth_result.method == "cinematic_passphrase":
                return f"🎉 Welcome back, {auth_result.user_id}. All systems are now at your command. "
            elif auth_result.method == "jwt_token":
                return f"Good {greeting}, {auth_result.user_id}. How may I assist you today? "
            else:
                return f"🔐 Master protocols activated for {auth_result.user_id}. Full administrative access granted. "
        
        elif auth_result.role == UserRole.STANDARD:
            return f"Hello! I'm ready to assist you. "
        
        return ""
    
    def filter_response_for_access_level(self, response: str, auth_result: AuthResult) -> str:
        """Filter response based on user access level with cinematic flair."""
        
        if not auth_result.authenticated:
            # Limited responses for unauthenticated users with cinematic touch
            limited_responses = [
                "I'm Buddy, your AI assistant. For full access, I need to verify your identity first.",
                "Hello! I can provide basic information, but my advanced capabilities require authentication.",
                "I'm here to help with general questions. For complete system access, please authenticate."
            ]
            
            if len(response) > 100 or any(word in response.lower() for word in ["personal", "history", "remember", "you"]):
                import random
                return random.choice(limited_responses)
        
        elif auth_result.role == UserRole.STANDARD:
            # Standard users get normal responses but no admin info
            if any(word in response.lower() for word in ["admin", "security", "whitelist", "logs"]):
                return "I can help with general questions and tasks. Administrative functions require master-level access."
        
        # Master users get full responses
        return response
    
    def override_conversation(self, master_auth: AuthResult, target_user: str) -> str:
        """Allow master to override another user's conversation."""
        if master_auth.role != UserRole.MASTER:
            return "❌ Only master user can override conversations."
        
        self.conversation_overrides[target_user] = master_auth.user_id
        return f"✅ Master override active for user: {target_user}"
    
    def check_conversation_override(self, user_id: str) -> Optional[str]:
        """Check if conversation is being overridden by master."""
        return self.conversation_overrides.get(user_id)
    
    def clear_conversation_override(self, user_id: str):
        """Clear conversation override."""
        if user_id in self.conversation_overrides:
            del self.conversation_overrides[user_id]