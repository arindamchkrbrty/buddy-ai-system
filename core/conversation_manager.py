import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ConversationSession:
    user_id: str
    authenticated: bool
    last_activity: datetime
    session_timeout: int = 30  # seconds
    role: str = "unknown"
    auth_method: str = "none"
    conversation_state: str = "idle"  # idle, awaiting_briefing_confirmation, etc.
    
    def is_expired(self) -> bool:
        """Check if session has expired based on inactivity."""
        if not self.authenticated:
            return True
        
        time_elapsed = (datetime.now() - self.last_activity).total_seconds()
        return time_elapsed > self.session_timeout
    
    def get_remaining_time(self) -> int:
        """Get remaining session time in seconds."""
        if not self.authenticated:
            return 0
        
        time_elapsed = (datetime.now() - self.last_activity).total_seconds()
        remaining = max(0, self.session_timeout - int(time_elapsed))
        return remaining
    
    def refresh_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()

class ConversationManager:
    """Manages sophisticated conversation flow with time-based authentication and daily briefings."""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
        
        # Daily briefing triggers
        self.briefing_triggers = [
            re.compile(r"good\s+(morning|afternoon|evening)\s+buddy", re.IGNORECASE),
            re.compile(r"morning\s+buddy", re.IGNORECASE),
            re.compile(r"afternoon\s+buddy", re.IGNORECASE),
            re.compile(r"evening\s+buddy", re.IGNORECASE)
        ]
        
        # Authentication trigger
        self.auth_trigger = re.compile(r"happy\s+birthday", re.IGNORECASE)
        
    def get_time_based_greeting(self) -> str:
        """Get appropriate greeting based on current time."""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            return "Good morning"
        elif 12 <= current_hour < 18:
            return "Good afternoon"
        elif 18 <= current_hour < 22:
            return "Good evening"
        else:  # 22-5 (late night/early morning)
            return "Good evening"
    
    def check_authentication(self, message: str, user_id: str = "default") -> Tuple[bool, Optional[str]]:
        """Check if message contains authentication trigger and handle session."""
        
        # Check for authentication phrase
        if self.auth_trigger.search(message):
            session = self._get_or_create_session(user_id)
            session.authenticated = True
            session.role = "master"
            session.auth_method = "cinematic_passphrase"
            session.refresh_activity()
            
            greeting = self.get_time_based_greeting()
            auth_response = f"🎉 Welcome back, Arindam. {greeting}! How may I assist you today?"
            
            logger.info(f"🎉 Cinematic authentication successful for {user_id}")
            return True, auth_response
        
        # Check existing session
        session = self.sessions.get(user_id)
        if session:
            if session.is_expired():
                # Session expired
                self._expire_session(user_id)
                return False, "⏰ Session expired. Please authenticate to continue."
            else:
                # Session is active, refresh activity
                session.refresh_activity()
                return True, None
        
        return False, None
    
    def check_daily_briefing_trigger(self, message: str, user_id: str = "default") -> Optional[str]:
        """Check if message triggers daily briefing request."""
        
        session = self.sessions.get(user_id)
        if not session or not session.authenticated:
            return None
        
        # Check for briefing triggers
        for trigger in self.briefing_triggers:
            if trigger.search(message):
                session.conversation_state = "awaiting_briefing_confirmation"
                session.refresh_activity()
                
                greeting = self.get_time_based_greeting()
                return f"{greeting}, Arindam! Would you like me to give you your daily briefing? I can share weather, upcoming meetings, and traffic updates."
        
        return None
    
    def handle_briefing_confirmation(self, message: str, user_id: str = "default") -> Optional[str]:
        """Handle user's response to briefing offer."""
        
        session = self.sessions.get(user_id)
        if not session or session.conversation_state != "awaiting_briefing_confirmation":
            return None
        
        message_lower = message.lower().strip()
        
        # Positive responses
        if any(word in message_lower for word in ["yes", "yeah", "sure", "please", "go ahead", "ok", "okay"]):
            session.conversation_state = "idle"
            session.refresh_activity()
            return self._generate_daily_briefing()
        
        # Negative responses
        elif any(word in message_lower for word in ["no", "nope", "not now", "later", "skip"]):
            session.conversation_state = "idle"
            session.refresh_activity()
            return "No problem! I'm here whenever you need assistance. What can I help you with today?"
        
        # Unclear response - ask for clarification
        else:
            session.refresh_activity()
            return "Would you like your daily briefing? Please say 'yes' or 'no'."
    
    def _generate_daily_briefing(self) -> str:
        """Generate mock daily briefing ready for real integrations."""
        current_time = datetime.now()
        greeting = self.get_time_based_greeting()
        
        briefing = f"""📋 **Your Daily Briefing** - {current_time.strftime('%A, %B %d, %Y')}

🌤️ **Weather Update:**
Today's weather: Partly cloudy, 72°F with a high of 78°F. Light breeze from the southwest at 8 mph. Perfect day for outdoor activities!
*[Ready for OpenWeatherMap API integration]*

📅 **Calendar Overview:**
• 10:00 AM - Team standup meeting (Conference Room A)
• 2:00 PM - Client presentation prep
• 4:30 PM - One-on-one with Sarah
• 6:00 PM - Dinner reservation at Bella Vista
*[Ready for Google Calendar/Outlook integration]*

🚗 **Traffic & Commute:**
Current traffic conditions: Light traffic on your usual routes. Estimated commute time to office: 22 minutes via Highway 101. Consider leaving by 9:30 AM for your 10:00 meeting.
*[Ready for Google Maps/Waze API integration]*

📊 **Quick Stats:**
• 3 unread priority emails
• Stock portfolio: +2.3% today
• Bitcoin: $43,250 (+1.8%)
*[Ready for email/financial API integrations]*

Is there anything specific you'd like me to elaborate on, Arindam?"""
        
        return briefing
    
    def get_session_status(self, user_id: str = "default") -> Dict:
        """Get current session status and information."""
        session = self.sessions.get(user_id)
        if not session:
            return {
                "authenticated": False,
                "session_active": False,
                "remaining_time": 0,
                "conversation_state": "idle"
            }
        
        return {
            "authenticated": session.authenticated,
            "session_active": not session.is_expired(),
            "remaining_time": session.get_remaining_time(),
            "conversation_state": session.conversation_state,
            "role": session.role,
            "auth_method": session.auth_method
        }
    
    def _get_or_create_session(self, user_id: str) -> ConversationSession:
        """Get existing session or create new one."""
        if user_id not in self.sessions:
            self.sessions[user_id] = ConversationSession(
                user_id=user_id,
                authenticated=False,
                last_activity=datetime.now()
            )
        return self.sessions[user_id]
    
    def _expire_session(self, user_id: str):
        """Expire and clean up session."""
        if user_id in self.sessions:
            logger.info(f"⏰ Session expired for user: {user_id}")
            del self.sessions[user_id]
    
    def cleanup_expired_sessions(self):
        """Clean up all expired sessions."""
        expired_sessions = []
        
        for user_id, session in self.sessions.items():
            if session.is_expired():
                expired_sessions.append(user_id)
        
        for user_id in expired_sessions:
            self._expire_session(user_id)
        
        if expired_sessions:
            logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
    
    def process_conversation_flow(self, message: str, user_id: str = "default") -> Optional[str]:
        """Main conversation flow processor."""
        
        # Clean up expired sessions first
        self.cleanup_expired_sessions()
        
        # Check authentication first
        is_authenticated, auth_response = self.check_authentication(message, user_id)
        if auth_response:
            return auth_response
        
        # If not authenticated, return None to let other systems handle
        if not is_authenticated:
            return None
        
        # Handle briefing confirmation if in that state
        briefing_response = self.handle_briefing_confirmation(message, user_id)
        if briefing_response:
            return briefing_response
        
        # Check for daily briefing trigger
        briefing_trigger_response = self.check_daily_briefing_trigger(message, user_id)
        if briefing_trigger_response:
            return briefing_trigger_response
        
        # If we get here, it's a normal conversation during active session
        session = self.sessions.get(user_id)
        if session and session.authenticated:
            session.refresh_activity()
        
        return None  # Let normal conversation flow continue
    
    def get_session_debug_info(self, user_id: str = "default") -> str:
        """Get session debug information for development."""
        status = self.get_session_status(user_id)
        
        if not status["authenticated"]:
            return ""
        
        remaining = status["remaining_time"]
        return f" [Session: Active - {remaining}s remaining]"