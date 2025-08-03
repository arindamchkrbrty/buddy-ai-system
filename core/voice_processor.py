import re
import logging
from typing import Dict, Optional, Tuple, List
from datetime import datetime

logger = logging.getLogger(__name__)

class VoiceProcessor:
    """Processes voice input and optimizes responses for iPhone/Siri integration."""
    
    def __init__(self):
        # Common voice-to-text corrections
        self.voice_corrections = {
            # Common speech-to-text errors
            "hey buddy": "hello buddy",
            "talk to buddy": "hello buddy", 
            "speak to buddy": "hello buddy",
            "buddy are you there": "hello buddy",
            
            # Authentication variations
            "happy birthday buddy": "happy birthday",
            "say happy birthday": "happy birthday",
            "it's happy birthday": "happy birthday",
            
            # Briefing variations
            "good morning body": "good morning buddy",
            "good afternoon body": "good afternoon buddy", 
            "good evening body": "good evening buddy",
            "morning briefing": "good morning buddy",
            "daily update": "good morning buddy",
            "what's my schedule": "good morning buddy",
            
            # Improvement variations
            "improve your self": "improve yourself",
            "make yourself better": "improve yourself",
            "upgrade your abilities": "improve yourself",
            "enhance your capabilities": "improve yourself"
        }
        
        # Speech fillers to remove
        self.speech_fillers = [
            r'\b(um|uh|er|ah|like|you know|actually|basically|literally)\b',
            r'\b(so|well|okay|alright|right)\s+',  # at start of phrases
            r'\s+(you know|like|um|uh)\s*$',  # at end of phrases
        ]
        
        # iPhone User-Agent patterns
        self.iphone_patterns = [
            re.compile(r'iPhone', re.IGNORECASE),
            re.compile(r'iOS', re.IGNORECASE),
            re.compile(r'Safari.*Mobile', re.IGNORECASE),
            re.compile(r'CFNetwork.*iOS', re.IGNORECASE)
        ]
        
        # Voice command patterns
        self.voice_commands = {
            'greeting': [
                re.compile(r'\b(hey|hi|hello|good morning|good afternoon|good evening)\s+(buddy|body)\b', re.IGNORECASE),
                re.compile(r'\bbuddy\s+(are you there|hello|hi)\b', re.IGNORECASE)
            ],
            'authentication': [
                re.compile(r'\bhappy\s+birthday\b', re.IGNORECASE),
                re.compile(r'\b(authenticate|login|sign in)\b', re.IGNORECASE)
            ],
            'briefing': [
                re.compile(r'\b(briefing|daily update|morning update|schedule|agenda)\b', re.IGNORECASE),
                re.compile(r'\b(what\'s my|tell me my|give me my)\s+(schedule|agenda|day)\b', re.IGNORECASE)
            ],
            'improvement': [
                re.compile(r'\b(improve|upgrade|enhance|make.*better)\b', re.IGNORECASE),
                re.compile(r'\bself.*improv', re.IGNORECASE)
            ]
        }
    
    def is_iphone_request(self, headers: Dict[str, str]) -> bool:
        """Detect if request comes from iPhone/iOS device."""
        user_agent = headers.get('user-agent', '').lower()
        
        # Check for iPhone patterns
        for pattern in self.iphone_patterns:
            if pattern.search(user_agent):
                return True
        
        # Check for Siri-specific headers
        siri_headers = [
            'x-siri-request',
            'x-apple-siri',
            'siri-ui-request-id'
        ]
        
        for header in siri_headers:
            if header in headers:
                return True
        
        return False
    
    def clean_voice_input(self, message: str) -> str:
        """Clean and normalize voice input from speech-to-text."""
        if not message:
            return ""
        
        cleaned = message.strip().lower()
        
        # Apply common voice corrections
        for incorrect, correct in self.voice_corrections.items():
            cleaned = re.sub(re.escape(incorrect), correct, cleaned, flags=re.IGNORECASE)
        
        # Remove speech fillers
        for filler_pattern in self.speech_fillers:
            cleaned = re.sub(filler_pattern, ' ', cleaned, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Restore original case for proper nouns and important words
        if 'buddy' in cleaned:
            cleaned = re.sub(r'\bbuddy\b', 'Buddy', cleaned, flags=re.IGNORECASE)
        if 'arindam' in cleaned:
            cleaned = re.sub(r'\barindam\b', 'Arindam', cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    def detect_voice_command_type(self, message: str) -> Optional[str]:
        """Detect the type of voice command."""
        message_clean = self.clean_voice_input(message)
        
        for command_type, patterns in self.voice_commands.items():
            for pattern in patterns:
                if pattern.search(message_clean):
                    return command_type
        
        return None
    
    def optimize_for_voice(self, response: str) -> str:
        """Optimize response for voice synthesis and iPhone/Siri."""
        if not response:
            return ""
        
        # Remove debug information
        response = re.sub(r'\s*\[Session:.*?\]', '', response)
        
        # Remove emojis and special characters
        response = self._remove_emojis(response)
        
        # Clean up markdown formatting
        response = self._clean_markdown(response)
        
        # Optimize for speech
        response = self._optimize_for_speech(response)
        
        # Ensure reasonable length for voice (under 30 seconds when spoken)
        response = self._limit_voice_length(response)
        
        return response.strip()
    
    def _remove_emojis(self, text: str) -> str:
        """Remove emojis and special characters."""
        # Remove common emojis
        emoji_patterns = [
            r'[\\U0001F600-\\U0001F64F]',  # emoticons
            r'[\\U0001F300-\\U0001F5FF]',  # symbols & pictographs
            r'[\\U0001F680-\\U0001F6FF]',  # transport & map
            r'[\\U0001F1E0-\\U0001F1FF]',  # flags
            r'[\\U00002702-\\U000027B0]',  # dingbats
            r'[\\U000024C2-\\U0001F251]',  # enclosed characters
            r'🎉|🎯|🚀|🔐|🔒|🔓|⏰|📋|🌤️|📅|🚗|📊|🤖|🎭|⚡|🧠|✅|❌|🎪|🛡️|🎬'
        ]
        
        for pattern in emoji_patterns:
            text = re.sub(pattern, '', text)
        
        # Remove special characters that don't read well
        text = re.sub(r'[•·▪▫]', '', text)  # bullet points
        text = re.sub(r'[★☆]', 'star', text)  # stars 
        text = re.sub(r'[→←↑↓]', '', text)  # arrows
        
        return text
    
    def _clean_markdown(self, text: str) -> str:
        """Clean markdown formatting for voice."""
        # Remove markdown bold/italic
        text = re.sub(r'\\*\\*(.*?)\\*\\*', r'\\1', text)  # **bold**
        text = re.sub(r'\\*(.*?)\\*', r'\\1', text)  # *italic*
        text = re.sub(r'_(.*?)_', r'\\1', text)  # _italic_
        
        # Convert headers to natural speech
        text = re.sub(r'^#{1,6}\\s*(.+)$', r'\\1.', text, flags=re.MULTILINE)
        
        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`([^`]+)`', r'\\1', text)
        
        # Convert lists to natural speech
        text = re.sub(r'^[-•*]\\s*(.+)$', r'\\1.', text, flags=re.MULTILINE)
        text = re.sub(r'^\\d+\\.\\s*(.+)$', r'\\1.', text, flags=re.MULTILINE)
        
        return text
    
    def _optimize_for_speech(self, text: str) -> str:
        """Optimize text for natural speech patterns."""
        # Add natural pauses
        text = re.sub(r'([.!?])\\s*([A-Z])', r'\\1 \\2', text)  # Ensure space after sentences
        
        # Convert abbreviations to speakable form
        abbreviations = {
            'API': 'A P I',
            'AI': 'A I',
            'UI': 'U I',
            'URL': 'U R L',
            'HTTP': 'H T T P',
            'JSON': 'Jason',
            'FAQ': 'F A Q',
            'CEO': 'C E O'
        }
        
        for abbr, spoken in abbreviations.items():
            text = re.sub(rf'\\b{abbr}\\b', spoken, text)
        
        # Make numbers more natural
        text = re.sub(r'\\b(\\d+)\\s*%', r'\\1 percent', text)
        text = re.sub(r'\\$(\\d+)', r'\\1 dollars', text)
        
        # Convert technical terms
        tech_terms = {
            'authentication': 'login process',
            'implementation': 'setup',
            'configuration': 'settings',
            'initialization': 'startup'
        }
        
        for technical, simple in tech_terms.items():
            text = re.sub(rf'\\b{technical}\\b', simple, text, flags=re.IGNORECASE)
        
        return text
    
    def _limit_voice_length(self, text: str, max_words: int = 200) -> str:
        """Limit response length for voice (roughly 30 seconds when spoken)."""
        words = text.split()
        
        if len(words) <= max_words:
            return text
        
        # Find a good breaking point
        sentences = re.split(r'[.!?]+', text)
        result = ""
        word_count = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            if word_count + sentence_words <= max_words:
                result += sentence.strip() + ". "
                word_count += sentence_words
            else:
                break
        
        # If we couldn't fit any complete sentences, just truncate
        if not result.strip():
            result = " ".join(words[:max_words]) + "..."
        
        return result.strip()
    
    def create_voice_confirmation(self, action: str) -> str:
        """Create voice-friendly confirmation responses."""
        confirmations = {
            'authentication': "Welcome back, Arindam. I'm ready to assist you.",
            'briefing_request': "I'll get your daily briefing ready. One moment please.",
            'improvement_start': "I'm ready to improve. What would you like me to work on?",
            'improvement_approved': "Great! I'll start working on that improvement right away.",
            'improvement_complete': "All done! Your improvement has been successfully implemented.",
            'session_expired': "Your session has expired. Please say happy birthday to continue.",
            'command_received': "Got it. Let me help you with that.",
            'error': "I'm sorry, I encountered an issue. Please try again."
        }
        
        return confirmations.get(action, "Understood. How can I help you?")
    
    def handle_voice_context(self, message: str, previous_context: Optional[str] = None) -> str:
        """Handle voice conversation context and references."""
        # Handle pronouns and references that make sense in voice context
        if previous_context:
            # Replace "that" or "it" with previous context if appropriate
            if re.search(r'\\b(do that|try that|implement that|proceed with that)\\b', message, re.IGNORECASE):
                if 'improvement' in previous_context.lower():
                    message = re.sub(r'\\b(do that|try that|implement that|proceed with that)\\b', 
                                   'proceed with the improvement', message, flags=re.IGNORECASE)
            
            # Handle "yes" and "no" with context
            if message.lower().strip() in ['yes', 'yeah', 'sure', 'okay', 'ok']:
                if 'briefing' in previous_context.lower():
                    message = "yes, give me the briefing"
                elif 'improvement' in previous_context.lower():
                    message = "yes, proceed with the improvement"
        
        return message
    
    def get_voice_response_format(self, response_type: str) -> Dict[str, str]:
        """Get voice-optimized response format for different types."""
        formats = {
            'greeting': {
                'prefix': '',
                'suffix': ' How can I help you today?'
            },
            'authentication': {
                'prefix': '',
                'suffix': ''
            },
            'briefing': {
                'prefix': 'Here is your daily briefing. ',
                'suffix': ' Is there anything else you need?'
            },
            'improvement': {
                'prefix': '',
                'suffix': ' What would you like me to do?'
            },
            'error': {
                'prefix': 'I apologize. ',
                'suffix': ' Please try again.'
            },
            'default': {
                'prefix': '',
                'suffix': ''
            }
        }
        
        return formats.get(response_type, formats['default'])