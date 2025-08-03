from abc import ABC, abstractmethod
from typing import Dict, Optional, Any

class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def generate_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate a response to a user message given context."""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the AI provider with configuration."""
        pass
    
    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about this AI provider."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the AI provider is healthy and available."""
        pass