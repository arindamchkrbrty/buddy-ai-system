import re
import logging
from typing import Dict, Optional, Tuple, List
from datetime import datetime

logger = logging.getLogger(__name__)

class VoiceProcessor:
    """Processes voice input and optimizes responses for iPhone/Siri integration.
    
    This class handles the complete voice processing pipeline for Buddy AI:
    
    **Input Processing:**
    - Cleans speech-to-text artifacts and errors
    - Corrects common voice recognition mistakes (\"body\" → \"buddy\")
    - Removes speech fillers (\"um\", \"uh\", \"like\")
    - Normalizes voice commands for consistent processing
    
    **Output Optimization:**
    - Removes visual elements (emojis, markdown, formatting)
    - Converts technical terms to speakable equivalents (\"API\" → \"A P I\")
    - Optimizes text for natural speech synthesis
    - Ensures clean, TTS-ready responses
    
    **Device Integration:**
    - Detects iPhone/iOS devices from User-Agent headers
    - Handles Siri-specific request patterns
    - Provides voice-optimized confirmation messages
    - Manages conversation context for voice interactions
    
    **Key Features:**
    - Speech-to-text error correction
    - Voice command pattern recognition  
    - iPhone device authentication support
    - Text-to-speech optimization
    - Conversation context handling
    """
    
    def __init__(self):
        """Initialize the voice processor with correction patterns and configurations.
        
        Sets up:
        - Voice-to-text correction mappings for common speech recognition errors
        - Speech filler removal patterns (um, uh, like, etc.)
        - iPhone User-Agent detection patterns
        - Voice command recognition patterns for different interaction types
        """
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
        """Detect if request comes from iPhone/iOS device.
        
        Analyzes HTTP headers to identify iPhone, iOS, and Siri requests.
        This enables device-specific optimizations and authentication priorities.
        
        Args:
            headers (Dict[str, str]): HTTP request headers dictionary
            
        Returns:
            bool: True if request comes from iPhone/iOS device, False otherwise
        """
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
        """Clean and normalize voice input from speech-to-text.
        
        Processes raw speech-to-text input to correct common recognition errors
        and normalize commands for consistent processing.
        
        Args:
            message (str): Raw speech-to-text input string
            
        Returns:
            str: Cleaned and normalized message ready for processing
        """
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
        """Detect the type of voice command for routing and processing.
        
        Analyzes cleaned voice input to determine the command category.
        
        Args:
            message (str): Cleaned voice input message
            
        Returns:
            Optional[str]: Command type ('greeting', 'authentication', 'briefing', 'improvement') or None
        """
        message_clean = self.clean_voice_input(message)
        
        for command_type, patterns in self.voice_commands.items():
            for pattern in patterns:
                if pattern.search(message_clean):
                    return command_type
        
        return None
    
    def optimize_for_voice(self, response: str) -> str:
        """Optimize response for voice synthesis and iPhone/Siri TTS.
        
        Complete voice optimization pipeline that transforms AI responses
        into clean, natural text suitable for text-to-speech synthesis.
        
        Args:
            response (str): Raw AI response with potential formatting
            
        Returns:
            str: Clean, TTS-ready text optimized for natural speech
        """
        if not response:
            return "I'm here to help. What can I do for you?"
        
        try:
            # Remove debug information first
            response = re.sub(r'\s*\[Session:.*?\]', '', response)
            
            # Remove emojis and special characters
            response = self._remove_emojis(response)
            
            # Clean up markdown formatting
            response = self._clean_markdown(response)
            
            # Optimize for speech
            response = self._optimize_for_speech(response)
            
            # Ensure reasonable length for voice (under 30 seconds when spoken)
            response = self._limit_voice_length(response)
            
            # Final cleanup - remove any remaining problematic characters
            response = self._final_cleanup(response)
            
            # Ensure we have clean, readable text
            if not response or len(response.strip()) < 3:
                return "I'm ready to help. What would you like to know?"
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error optimizing voice response: {e}")
            # Return safe fallback response
            return "I'm here and ready to assist you. How can I help?"
    
    def _remove_emojis(self, text: str) -> str:
        """Remove emojis and special characters."""
        try:
            # Simple approach: remove common emojis explicitly
            emoji_chars = ['🎉', '🎯', '🚀', '🔐', '🔒', '🔓', '⏰', '📋', '🌤️', '📅', '🚗', '📊', '🤖', '🎭', '⚡', '🧠', '✅', '❌', '🎪', '🛡️', '🎬']
            
            for emoji in emoji_chars:
                text = text.replace(emoji, '')
            
            # Remove special characters that don't read well
            text = re.sub(r'[•·▪▫]', '', text)  # bullet points
            text = re.sub(r'[★☆]', 'star', text)  # stars 
            text = re.sub(r'[→←↑↓]', '', text)  # arrows
            
            # Remove any remaining emoji-like characters (high unicode)
            text = ''.join(char for char in text if ord(char) < 256 or char.isalpha())
            
            return text
            
        except Exception as e:
            logger.error(f"Error removing emojis: {e}")
            return text
    
    def _clean_markdown(self, text: str) -> str:
        """Clean markdown formatting for voice."""
        try:
            # Remove markdown bold/italic - FIXED: Using proper backreferences
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
            text = re.sub(r'\*(.*?)\*', r'\1', text)  # *italic*
            text = re.sub(r'_(.*?)_', r'\1', text)  # _italic_
            
            # Convert headers to natural speech
            text = re.sub(r'^#{1,6}\s*(.+)$', r'\1.', text, flags=re.MULTILINE)
            
            # Remove code blocks
            text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
            text = re.sub(r'`([^`]+)`', r'\1', text)
            
            # Convert lists to natural speech
            text = re.sub(r'^[-•*]\s*(.+)$', r'\1. ', text, flags=re.MULTILINE)
            text = re.sub(r'^\d+\.\s*(.+)$', r'\1. ', text, flags=re.MULTILINE)
            
            return text
        except Exception as e:
            logger.error(f"Error cleaning markdown: {e}")
            # Return original text if cleaning fails
            return text
    
    def _optimize_for_speech(self, text: str) -> str:
        """Optimize text for natural speech patterns."""
        try:
            # Add natural pauses - FIXED: Proper regex patterns
            text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)  # Ensure space after sentences
            
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
                text = re.sub(rf'\b{re.escape(abbr)}\b', spoken, text)
            
            # Make numbers more natural - FIXED: Proper regex patterns
            text = re.sub(r'\b(\d+)\s*%', r'\1 percent', text)
            text = re.sub(r'\$(\d+)', r'\1 dollars', text)
            
            # Convert technical terms
            tech_terms = {
                'authentication': 'login process',
                'implementation': 'setup',  
                'configuration': 'settings',
                'initialization': 'startup'
            }
            
            for technical, simple in tech_terms.items():
                text = re.sub(rf'\b{re.escape(technical)}\b', simple, text, flags=re.IGNORECASE)
            
            return text
        except Exception as e:
            logger.error(f"Error optimizing for speech: {e}")
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
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup to ensure clean text output."""
        try:
            # Remove any remaining escape sequences (but preserve regular text)
            text = re.sub(r'\\[nrtbfav]', ' ', text)  # Convert escape sequences to spaces
            text = re.sub(r'\\[0-9]+', '', text)  # Remove numbered escape sequences like \1, \2
            text = re.sub(r'\\{2,}', '', text)  # Remove multiple backslashes
            
            # Clean up excessive whitespace
            text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
            text = re.sub(r'\n+', ' ', text)  # Newlines to spaces
            text = re.sub(r'\t+', ' ', text)  # Tabs to spaces
            
            # Remove problematic punctuation sequences
            text = re.sub(r'[.]{2,}', '.', text)  # Multiple dots to single dot
            text = re.sub(r'[!]{2,}', '!', text)  # Multiple exclamations to single
            text = re.sub(r'[?]{2,}', '?', text)  # Multiple questions to single
            
            # Ensure proper sentence structure - capitalize after sentence endings
            text = re.sub(r'([.!?])\s*([a-z])', lambda m: m.group(1) + ' ' + m.group(2).upper(), text)
            
            # Remove any remaining non-printable characters except spaces
            text = ''.join(char for char in text if char.isprintable() or char.isspace())
            
            # Fix any remaining issues with missing first characters
            if text and not text[0].isupper() and text[0].isalpha():
                text = text[0].upper() + text[1:]
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error in final cleanup: {e}")
            return text
    
    def create_voice_confirmation(self, action: str) -> str:
        """Create voice-friendly confirmation responses for system actions.
        
        Args:
            action (str): Action type requiring confirmation
            
        Returns:
            str: Voice-optimized confirmation message
        """
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
        """Handle voice conversation context and pronoun resolution.
        
        Args:
            message (str): Current voice input message
            previous_context (Optional[str]): Previous conversation context
            
        Returns:
            str: Message with resolved context and pronouns
        """
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
        """Get voice-optimized response format templates.
        
        Args:
            response_type (str): Type of response to format
            
        Returns:
            Dict[str, str]: Format dictionary with 'prefix' and 'suffix' keys
        """
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