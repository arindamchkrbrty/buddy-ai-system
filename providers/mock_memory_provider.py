from typing import Dict, List, Any, Optional
from datetime import datetime
from .memory_provider import MemoryProvider

class MockMemoryProvider(MemoryProvider):
    """Mock memory provider for testing and development."""
    
    def __init__(self):
        self.name = "Mock Memory Provider"
        self.version = "1.0.0"
        self.initialized = False
        
        # In-memory storage (will be lost on restart)
        self._conversations: Dict[str, List[Dict[str, Any]]] = {}
        self._preferences: Dict[str, Dict[str, Any]] = {}
    
    async def store_interaction(self, user_id: str, message: str, response: str) -> bool:
        """Store a user interaction in memory."""
        try:
            if user_id not in self._conversations:
                self._conversations[user_id] = []
            
            interaction = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "response": response,
                "type": "conversation"
            }
            
            self._conversations[user_id].append(interaction)
            
            # Keep only last 100 interactions per user
            if len(self._conversations[user_id]) > 100:
                self._conversations[user_id] = self._conversations[user_id][-100:]
            
            return True
        except Exception:
            return False
    
    async def get_context(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get conversation context for a user."""
        history = await self.get_conversation_history(user_id, limit)
        preferences = await self.get_user_preferences(user_id)
        
        return {
            "user_id": user_id,
            "conversation_history": history,
            "user_preferences": preferences,
            "session_start": datetime.now().isoformat(),
            "total_interactions": len(self._conversations.get(user_id, []))
        }
    
    async def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for a user."""
        if user_id not in self._conversations:
            return []
        
        # Return the most recent interactions
        return self._conversations[user_id][-limit:] if limit > 0 else self._conversations[user_id]
    
    async def store_user_preference(self, user_id: str, key: str, value: Any) -> bool:
        """Store a user preference."""
        try:
            if user_id not in self._preferences:
                self._preferences[user_id] = {}
            
            self._preferences[user_id][key] = {
                "value": value,
                "timestamp": datetime.now().isoformat()
            }
            return True
        except Exception:
            return False
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get all user preferences."""
        if user_id not in self._preferences:
            return {}
        
        # Return just the values, not the metadata
        return {
            key: data["value"] 
            for key, data in self._preferences[user_id].items()
        }
    
    async def clear_user_data(self, user_id: str) -> bool:
        """Clear all data for a user."""
        try:
            if user_id in self._conversations:
                del self._conversations[user_id]
            if user_id in self._preferences:
                del self._preferences[user_id]
            return True
        except Exception:
            return False
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the mock memory provider."""
        self.initialized = True
        return True
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about this mock provider."""
        return {
            "name": self.name,
            "version": self.version,
            "type": "mock",
            "storage": "in-memory",
            "capabilities": [
                "Conversation history storage",
                "User preferences",
                "Session context"
            ],
            "limitations": [
                "Data lost on restart",
                "No persistence",
                "Limited to single instance"
            ],
            "stats": {
                "total_users": len(self._conversations),
                "total_conversations": sum(len(conv) for conv in self._conversations.values())
            }
        }