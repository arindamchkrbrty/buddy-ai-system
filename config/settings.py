import os
from typing import Optional

class Settings:
    """Configuration settings for Buddy AI Agent."""
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # AI Provider Configuration
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "huggingface")
    AI_PROVIDER_API_KEY: Optional[str] = os.getenv("AI_PROVIDER_API_KEY")
    AI_PROVIDER_MODEL: str = os.getenv("AI_PROVIDER_MODEL", "default")
    AI_PROVIDER_BASE_URL: Optional[str] = os.getenv("AI_PROVIDER_BASE_URL")
    
    # Memory Provider Configuration
    MEMORY_PROVIDER: str = os.getenv("MEMORY_PROVIDER", "mock")
    MEMORY_PROVIDER_URL: Optional[str] = os.getenv("MEMORY_PROVIDER_URL")
    MEMORY_PROVIDER_API_KEY: Optional[str] = os.getenv("MEMORY_PROVIDER_API_KEY")
    
    # Buddy Configuration
    BUDDY_NAME: str = os.getenv("BUDDY_NAME", "Buddy")
    BUDDY_PERSONALITY_LEVEL: str = os.getenv("BUDDY_PERSONALITY_LEVEL", "friendly")
    MAX_CONVERSATION_HISTORY: int = int(os.getenv("MAX_CONVERSATION_HISTORY", "50"))
    
    # Security Configuration
    API_KEY: Optional[str] = os.getenv("API_KEY")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    
    # Authentication Configuration
    MASTER_USER: str = os.getenv("MASTER_USER", "Arindam")
    MASTER_PASSPHRASE: str = os.getenv("MASTER_PASSPHRASE", "happy birthday")
    MASTER_DEVICES: str = os.getenv("MASTER_DEVICES", "iPhone14,7,iPhone14,2,iPhone14,3,iPhone15,2,iPhone15,3,iPhone16,1,iPhone16,2")
    ENABLE_DEVICE_AUTH: bool = os.getenv("ENABLE_DEVICE_AUTH", "true").lower() == "true"
    ENABLE_VOICE_AUTH: bool = os.getenv("ENABLE_VOICE_AUTH", "true").lower() == "true"
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    @classmethod
    def get_ai_provider_config(cls) -> dict:
        """Get AI provider specific configuration."""
        return {
            "provider": cls.AI_PROVIDER,
            "api_key": cls.AI_PROVIDER_API_KEY,
            "model": cls.AI_PROVIDER_MODEL,
            "base_url": cls.AI_PROVIDER_BASE_URL,
        }
    
    @classmethod
    def get_memory_provider_config(cls) -> dict:
        """Get memory provider specific configuration."""
        return {
            "provider": cls.MEMORY_PROVIDER,
            "url": cls.MEMORY_PROVIDER_URL,
            "api_key": cls.MEMORY_PROVIDER_API_KEY,
            "max_history": cls.MAX_CONVERSATION_HISTORY,
        }
    
    @classmethod
    def get_buddy_config(cls) -> dict:
        """Get Buddy specific configuration."""
        return {
            "name": cls.BUDDY_NAME,
            "personality_level": cls.BUDDY_PERSONALITY_LEVEL,
            "max_conversation_history": cls.MAX_CONVERSATION_HISTORY,
        }
    
    @classmethod
    def get_auth_config(cls) -> dict:
        """Get authentication specific configuration."""
        return {
            "master_user": cls.MASTER_USER,
            "master_passphrase": cls.MASTER_PASSPHRASE,
            "master_devices": cls.MASTER_DEVICES.split(",") if cls.MASTER_DEVICES else [],
            "enable_device_auth": cls.ENABLE_DEVICE_AUTH,
            "enable_voice_auth": cls.ENABLE_VOICE_AUTH,
        }

# Global settings instance
settings = Settings()