"""
Configuration settings for the application.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    """Application settings."""
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Event Analytics API"
    VERSION: str = "1.0.0"
    
    # Database settings
    DATABASE_URL: str = "postgresql://events_user:events_password@localhost:5433/events"
    
    # Redis settings (для rate limiting)
    REDIS_URL: Optional[str] = None
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 1000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Development settings
    DEBUG: bool = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
