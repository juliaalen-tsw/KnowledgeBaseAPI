"""
config.py
---------
This file reads all configuration from environment variables.
pydantic-settings automatically loads .env files and validates types.
Think of this like a TypeScript interface that also reads process.env.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/knowledge_base"

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT settings
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS - stored as a comma-separated string in env, parsed into a list
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # App environment
    APP_ENV: str = "development"

    # pydantic-settings will automatically read from a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins_list(self) -> list[str]:
        """Convert the comma-separated CORS_ORIGINS string into a Python list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# lru_cache means this function only runs once; subsequent calls return the cached result.
# This prevents re-reading the .env file on every request.
@lru_cache()
def get_settings() -> Settings:
    return Settings()
