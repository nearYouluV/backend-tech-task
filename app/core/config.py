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
        case_sensitive=True,
        extra="ignore"  
    )
    
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Event Analytics API"
    VERSION: str = "1.0.0"
    
    POSTGRES_USER: str = Field(..., description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(..., description="PostgreSQL password")
    POSTGRES_DB: str = Field(default="events", description="PostgreSQL database name")
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: str = Field(default="5432", description="PostgreSQL port")
    
    # External ports (for Docker)
    APP_EXTERNAL_PORT: str = Field(default="8000", description="External application port")
    
    # Rate limiting  
    RATE_LIMIT_PER_MINUTE: int = Field(default=1000, description="Rate limit per minute")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # Development settings
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    # JWT Authentication
    JWT_SECRET_KEY: str = Field(..., description="JWT secret key for token signing")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="JWT access token expiration in minutes")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="JWT refresh token expiration in days")
    
    # ClickHouse settings (cold storage)
    CLICKHOUSE_HOST: str = Field(default="localhost", description="ClickHouse host")
    CLICKHOUSE_PORT: int = Field(default=8123, description="ClickHouse HTTP port")
    CLICKHOUSE_DB: str = Field(default="events_analytics", description="ClickHouse database name")
    CLICKHOUSE_USER: str = Field(default="default", description="ClickHouse username")
    CLICKHOUSE_PASSWORD: Optional[str] = Field(default="", description="ClickHouse password")
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from components."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property 
    def CLICKHOUSE_URL(self) -> str:
        """Construct ClickHouse URL from components."""
        if self.CLICKHOUSE_PASSWORD:
            return f"clickhouse://{self.CLICKHOUSE_USER}:{self.CLICKHOUSE_PASSWORD}@{self.CLICKHOUSE_HOST}:{self.CLICKHOUSE_PORT}/{self.CLICKHOUSE_DB}"
        return f"clickhouse://{self.CLICKHOUSE_USER}@{self.CLICKHOUSE_HOST}:{self.CLICKHOUSE_PORT}/{self.CLICKHOUSE_DB}"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
