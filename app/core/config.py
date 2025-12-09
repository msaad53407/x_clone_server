"""
Application configuration settings using Pydantic Settings.
Loads environment variables from .env file.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # App Settings
    app_name: str = "X Clone API"
    debug: bool = False
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Database
    database_url: str
    
    # Email (Resend API)
    resend_api_key: str = ""
    resend_from_email: str = "noreply@yourdomain.com"
    
    # Frontend URL (for email verification links)
    frontend_url: str = "http://localhost:5173"
    
    # Cloudinary
    cloudinary_url: str = ""
    
    @property
    def async_database_url(self) -> str:
        """Ensure database URL uses asyncpg driver."""
        url = self.database_url
        # Handle postgres:// (used by many cloud providers like Heroku, Sevalla)
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        # Handle postgresql:// (standard format)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
