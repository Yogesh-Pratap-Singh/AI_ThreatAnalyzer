import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database Settings
    DATABASE_URL: str = "postgresql+asyncpg://postgres:rpdyn%401210@localhost:5432/threat_analyzer"
    DATABASE_SYNC_URL: str = "postgresql://postgres:rpdyn%401210@localhost:5432/threat_analyzer"

    # Redis Mock (fallback to in-memory if empty/unreachable)
    REDIS_URL: Optional[str] = None

    # Kafka Settings (defaults to in-memory asyncio.Queue if disabled)
    KAFKA_BOOTSTRAP_SERVERS: Optional[str] = None
    KAFKA_GROUP_ID: str = "threat-analyzer-workers"

    # Security & Auth
    JWT_SECRET_KEY: str = "supersecretkeyforthreatanalyzerdevelopment12345!"
    JWT_REFRESH_SECRET_KEY: str = "supersecretrefreshkeyforthreatanalyzerdevelopment12345!"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_HOURS: int = 8

    # AI / OpenRouter API
    OPENROUTER_API_KEY: Optional[str] = None
    LLM_MODEL: str = "anthropic/claude-3.5-sonnet"
    LLM_MAX_TOKENS: int = 300

    # Severity Scoring & Baseline
    ANOMALY_THRESHOLD: float = 0.75

    # App Settings
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

settings = Settings()
