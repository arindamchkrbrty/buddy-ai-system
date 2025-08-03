from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

class MemoryProvider(ABC):
    """Abstract base class for memory providers."""
    
    @abstractmethod
    async def store_interaction(self, user_id: str, message: str, response: str) -> bool:
        """Store a user interaction (message and response)."""
        pass
    
    @abstractmethod
    async def get_context(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get conversation context for a user."""
        pass
    
    @abstractmethod
    async def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for a user."""
        pass
    
    @abstractmethod
    async def store_user_preference(self, user_id: str, key: str, value: Any) -> bool:
        """Store a user preference."""
        pass
    
    @abstractmethod
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get all user preferences."""
        pass
    
    @abstractmethod
    async def clear_user_data(self, user_id: str) -> bool:
        """Clear all data for a user."""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the memory provider with configuration."""
        pass
    
    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about this memory provider."""
        pass