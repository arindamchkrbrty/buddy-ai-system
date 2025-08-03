import random
from typing import Dict, Any
from .ai_provider import AIProvider

class MockAIProvider(AIProvider):
    """Mock AI provider for testing and development."""
    
    def __init__(self):
        self.name = "Mock AI Provider"
        self.version = "1.0.0"
        self.initialized = False
    
    async def generate_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate a mock response based on the message."""
        message_lower = message.lower()
        
        if "hello" in message_lower or "hi" in message_lower:
            responses = [
                "Hello! Great to meet you!",
                "Hi there! How are you doing today?",
                "Hey! What's on your mind?",
                "Hello! I'm excited to chat with you!"
            ]
        elif "help" in message_lower:
            responses = [
                "I'm here to help! What do you need assistance with?",
                "Sure thing! How can I assist you today?",
                "I'd love to help! What's the challenge you're facing?"
            ]
        elif "weather" in message_lower:
            responses = [
                "I don't have real weather data, but I hope it's beautiful where you are!",
                "While I can't check the weather, I'd recommend looking outside or checking a weather app!",
                "I wish I could tell you about the weather, but that's beyond my current capabilities!"
            ]
        elif "name" in message_lower:
            responses = [
                "I'm Buddy, your friendly AI assistant!",
                "You can call me Buddy! I'm here to help.",
                "I'm Buddy - nice to meet you!"
            ]
        else:
            responses = [
                "That's interesting! Tell me more about what you're thinking.",
                "I understand what you're saying. How can I help you with that?",
                "Thanks for sharing that with me! What would you like to explore further?",
                "That's a great point! What else is on your mind?",
                "I appreciate you bringing that up. How can I assist you?"
            ]
        
        return random.choice(responses)
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the mock AI provider."""
        self.initialized = True
        return True
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about this mock provider."""
        return {
            "name": self.name,
            "version": self.version,
            "type": "mock",
            "capabilities": [
                "Basic conversation",
                "Simple pattern matching",
                "Random response selection"
            ],
            "limitations": [
                "No real AI processing",
                "Limited response variety",
                "No learning capabilities"
            ]
        }
    
    async def health_check(self) -> bool:
        """Check if the mock provider is available."""
        return self.initialized