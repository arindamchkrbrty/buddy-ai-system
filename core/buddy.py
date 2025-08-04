import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime

from providers.ai_provider import AIProvider
from providers.memory_provider import MemoryProvider
from config.settings import settings
from .conversation_manager import ConversationManager
from .self_improvement import SelfImprovementManager
from .voice_processor import VoiceProcessor

logger = logging.getLogger(__name__)

class Buddy:
    """Main AI agent class that orchestrates conversation, authentication, and system features.
    
    Buddy is the central coordinator that integrates:
    - AI conversation processing (HuggingFace DialoGPT or fallback responses)
    - Voice processing pipeline for iPhone/Siri integration
    - Sophisticated conversation management with time-based greetings
    - Self-improvement system for code modification
    - Authentication integration and session management
    
    **Core Capabilities:**
    - Natural conversation with personality-driven responses
    - Daily briefing system with time-aware greetings
    - Voice command processing and optimization
    - Self-modification and improvement workflows
    - Multi-provider AI backend support
    - Memory and context management
    
    **Processing Flow:**
    1. Self-improvement trigger check
    2. Conversation manager (greetings, briefings, sessions)
    3. AI provider processing (HuggingFace or fallback)
    4. Voice optimization (if voice request)
    5. Personality application and response formatting
    """
    
    def __init__(self):
        """Initialize Buddy with personality, providers, and processing components.
        
        Sets up:
        - Personality traits and communication style
        - AI and memory provider initialization
        - Conversation manager for session handling
        - Self-improvement system for code modification
        - Voice processor for iPhone/Siri integration
        """
        self.name = "Buddy"
        self.personality = {
            "traits": [
                "helpful", "friendly", "curious", "patient", "encouraging"
            ],
            "communication_style": "conversational and warm",
            "expertise": "general assistance and problem-solving",
            "goal": "to be a reliable and supportive AI companion"
        }
        
        self.ai_provider: Optional[AIProvider] = None
        self.memory_provider: Optional[MemoryProvider] = None
        self.conversation_manager = ConversationManager()
        self.self_improvement = SelfImprovementManager()
        self.voice_processor = VoiceProcessor()
        
        self._initialize_providers()
    
    def _initialize_providers(self):
        try:
            # Initialize AI Provider
            if settings.AI_PROVIDER == "huggingface":
                from providers.huggingface_provider import HuggingFaceProvider
                self.ai_provider = HuggingFaceProvider()
                # Initialize the provider asynchronously
                asyncio.create_task(self._initialize_ai_provider())
            elif settings.AI_PROVIDER == "mock":
                from providers.mock_ai_provider import MockAIProvider
                self.ai_provider = MockAIProvider()
            
            # Initialize Memory Provider
            if settings.MEMORY_PROVIDER == "mock":
                from providers.mock_memory_provider import MockMemoryProvider
                self.memory_provider = MockMemoryProvider()
                
            logger.info(f"Buddy initialized with {settings.AI_PROVIDER} AI provider and {settings.MEMORY_PROVIDER} memory provider")
        except Exception as e:
            logger.error(f"Failed to initialize providers: {e}")
            self.ai_provider = None
            self.memory_provider = None
    
    async def _initialize_ai_provider(self):
        """Initialize AI provider asynchronously."""
        if self.ai_provider and hasattr(self.ai_provider, 'initialize'):
            try:
                config = settings.get_ai_provider_config()
                success = await self.ai_provider.initialize(config)
                if success:
                    logger.info("AI provider initialized successfully")
                else:
                    logger.error("AI provider initialization failed")
            except Exception as e:
                logger.error(f"Error initializing AI provider: {e}")
    
    async def process_message(self, message: str, user_id: str = "default", auth_result = None, is_voice: bool = False, headers: Dict = None) -> str:
        """Process user message through complete conversation pipeline.
        
        This is Buddy's main message processing method that coordinates:
        1. Voice input cleaning (if voice request)
        2. Self-improvement workflow checking
        3. Conversation manager processing (greetings, briefings, sessions)
        4. AI provider response generation
        5. Voice optimization (if voice request)
        6. Session debug information (if not voice)
        
        Args:
            message (str): User's input message or command
            user_id (str): User identifier for context and memory
            auth_result: Authentication result object with user permissions
            is_voice (bool): Whether this is a voice request requiring TTS optimization
            headers (Dict): HTTP headers for device detection and processing
            
        Returns:
            str: Processed response optimized for the request type (voice or text)
            
        Processing Priority:
        1. **Self-improvement**: Checks for improvement triggers first
        2. **Conversation flow**: Time-based greetings, briefings, session management
        3. **AI processing**: Routes to AI provider or fallback responses
        4. **Voice optimization**: TTS preparation for voice requests
        """
        try:
            # Clean voice input if this is a voice request
            if is_voice and headers:
                original_message = message
                message = self.voice_processor.clean_voice_input(message)
                
                # Detect voice command type for better processing
                command_type = self.voice_processor.detect_voice_command_type(message)
                logger.info(f"Voice command detected: {command_type} | Original: '{original_message}' | Cleaned: '{message}'")
            
            # First check self-improvement flow
            improvement_response = self.self_improvement.check_improvement_trigger(message, user_id)
            if improvement_response:
                if is_voice:
                    improvement_response = self.voice_processor.optimize_for_voice(improvement_response)
                return improvement_response
            
            # Check if in improvement flow
            improvement_flow_response = self.self_improvement.process_improvement_request(message, user_id)
            if improvement_flow_response:
                if is_voice:
                    improvement_flow_response = self.voice_processor.optimize_for_voice(improvement_flow_response)
                return improvement_flow_response
            
            # Then check sophisticated conversation flow
            conversation_response = self.conversation_manager.process_conversation_flow(message, user_id)
            if conversation_response:
                if is_voice:
                    conversation_response = self.voice_processor.optimize_for_voice(conversation_response)
                else:
                    # Add session debug info for development (not for voice)
                    debug_info = self.conversation_manager.get_session_debug_info(user_id)
                    conversation_response += debug_info
                return conversation_response
            
            context = await self._get_context(user_id)
            
            # Add authentication info to context if available
            if auth_result:
                context["auth_info"] = {
                    "authenticated": auth_result.authenticated,
                    "user_id": auth_result.user_id,
                    "role": auth_result.role.value,
                    "method": auth_result.method,
                    "device_id": auth_result.device_id
                }
            
            # Add conversation session info to context
            session_status = self.conversation_manager.get_session_status(user_id)
            context["session_info"] = session_status
            
            # For HuggingFace provider, use the original message to avoid confusing the model
            if hasattr(self.ai_provider, 'model_name') and 'DialoGPT' in str(getattr(self.ai_provider, 'model_name', '')):
                input_message = message
            else:
                input_message = self._enhance_message_with_personality(message, context)
            
            if self.ai_provider:
                response = await self.ai_provider.generate_response(input_message, context)
            else:
                response = self._fallback_response(message)
            
            await self._store_interaction(user_id, message, response)
            
            final_response = self._apply_personality_to_response(response)
            
            # Optimize for voice if needed
            if is_voice:
                final_response = self.voice_processor.optimize_for_voice(final_response)
            else:
                # Add session debug info for development (not for voice)
                debug_info = self.conversation_manager.get_session_debug_info(user_id)
                final_response += debug_info
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._error_response()
    
    def _enhance_message_with_personality(self, message: str, context: Dict) -> str:
        personality_context = f"""
You are {self.name}, an AI assistant with the following characteristics:
- Traits: {', '.join(self.personality['traits'])}
- Communication style: {self.personality['communication_style']}
- Expertise: {self.personality['expertise']}
- Goal: {self.personality['goal']}

Please respond in a way that reflects these characteristics while being helpful and accurate.

User message: {message}
"""
        return personality_context
    
    def _apply_personality_to_response(self, response: str) -> str:
        if not response:
            return "I'm here to help! What would you like to know or discuss?"
        
        friendly_starters = [
            "I'd be happy to help! ",
            "Great question! ",
            "I'm glad you asked! ",
            ""
        ]
        
        if not any(response.startswith(starter.strip()) for starter in friendly_starters):
            import random
            starter = random.choice(friendly_starters[:-1])
            if not response[0].isupper():
                response = response[0].upper() + response[1:]
            response = starter + response
        
        return response
    
    def _fallback_response(self, message: str) -> str:
        fallback_responses = {
            "hello": "Hello! I'm Buddy, your AI assistant. How can I help you today?",
            "hi": "Hi there! I'm Buddy. What can I do for you?",
            "help": "I'm here to help! I can assist with various tasks and answer questions. What would you like to know?",
            "who are you": f"I'm {self.name}, your friendly AI assistant. I'm designed to be helpful, curious, and supportive. How can I assist you today?",
            "default": "I'm having trouble processing your request right now, but I'm here to help! Could you try rephrasing your question?"
        }
        
        message_lower = message.lower().strip()
        for key, response in fallback_responses.items():
            if key in message_lower:
                return response
        
        return fallback_responses["default"]
    
    def _error_response(self) -> str:
        return "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment!"
    
    async def _get_context(self, user_id: str) -> Dict:
        if self.memory_provider:
            try:
                return await self.memory_provider.get_context(user_id)
            except Exception as e:
                logger.error(f"Failed to retrieve context: {e}")
        
        return {
            "user_id": user_id,
            "conversation_history": [],
            "user_preferences": {},
            "session_start": datetime.now().isoformat()
        }
    
    async def _store_interaction(self, user_id: str, message: str, response: str):
        if self.memory_provider:
            try:
                await self.memory_provider.store_interaction(user_id, message, response)
            except Exception as e:
                logger.error(f"Failed to store interaction: {e}")
    
    def get_personality_info(self) -> Dict:
        """Get comprehensive information about Buddy's personality and capabilities.
        
        Returns:
            Dict: Complete personality profile including traits, capabilities,
                  self-improvement status, and future expansion plans
        """
        return {
            "name": self.name,
            "personality": self.personality,
            "capabilities": [
                "General conversation",
                "Question answering",
                "Task assistance",
                "Problem solving"
            ],
            "future_expansions": [
                "Specialist agent integration",
                "Advanced memory management",
                "Multi-modal capabilities",
                "Tool usage"
            ],
            "self_improvement": {
                "status": self.self_improvement.get_improvement_status(),
                "capabilities": [
                    "Conversation enhancement",
                    "Personality development", 
                    "New functionality addition",
                    "Daily briefing improvements",
                    "Integration preparation"
                ]
            }
        }
    
    def get_status(self) -> Dict:
        """Get current operational status of Buddy's components.
        
        Returns:
            Dict: System status including provider initialization and readiness
        """
        return {
            "name": self.name,
            "ai_provider": self.ai_provider.__class__.__name__ if self.ai_provider else "None",
            "memory_provider": self.memory_provider.__class__.__name__ if self.memory_provider else "None",
            "initialized": self.ai_provider is not None and self.memory_provider is not None
        }