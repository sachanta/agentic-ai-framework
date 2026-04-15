"""
Application configuration settings.
"""
import logging
import re
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_INSECURE_SECRET_KEY_DEFAULTS = {
    "your-secret-key-change-in-production",
    "changeme",
    "secret",
    "",
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Agentic AI Framework"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # CORS - stored as comma-separated string, parsed via property
    CORS_ORIGINS_STR: str = "http://localhost:5173,http://localhost:3000"

    # Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "agentic_ai"

    # Weaviate
    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_API_KEY: str | None = None

    # LLM Configuration (provider-agnostic)
    LLM_PROVIDER: str = "gemini"  # gemini | perplexity | ollama | openai | aws_bedrock
    LLM_DEFAULT_MODEL: str = "gemini-2.0-flash"  # Default model for chosen provider
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 1000
    LLM_TIMEOUT: float = 120.0

    # Gemini Configuration (default provider)
    GEMINI_API_KEY: str | None = None
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"

    # Perplexity Configuration (Sonar models with search)
    PERPLEXITY_API_KEY: str | None = None
    PERPLEXITY_BASE_URL: str = "https://api.perplexity.ai"

    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # OpenAI Configuration
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # AWS Bedrock Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_BEDROCK_MODEL: str = "anthropic.claude-v2"

    # System Email (Resend)
    RESEND_API_KEY: str | None = None
    SYSTEM_FROM_EMAIL: str = "noreply@example.com"
    SYSTEM_FROM_NAME: str = "Agentic AI Framework"

    # Signup & Approval
    SIGNUP_APPROVAL_EMAIL: str = "achantas@gmail.com"
    APP_BASE_URL: str = "http://localhost:8000"
    SIGNUP_APPROVAL_TOKEN_EXPIRY_DAYS: int = 7
    SIGNUP_AVAILABLE_PLATFORMS: str = "newsletter,hello_world"

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parse CORS_ORIGINS from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",") if origin.strip()]

    def validate_secret_key(self) -> None:
        """Validate that SECRET_KEY has been changed from the insecure default."""
        if self.SECRET_KEY.lower().strip() in _INSECURE_SECRET_KEY_DEFAULTS:
            raise RuntimeError(
                "SECURITY ERROR: SECRET_KEY is set to an insecure default value. "
                "Set a strong, unique SECRET_KEY via environment variable "
                "before running in production."
            )
        if len(self.SECRET_KEY) < 32:
            logger.warning(
                "SECRET_KEY is shorter than 32 characters. "
                "Consider using a longer key for better security."
            )

    @staticmethod
    def sanitize_mongodb_uri(uri: str) -> str:
        """Remove credentials from a MongoDB URI for safe logging."""
        return re.sub(
            r"://[^@]+@",
            "://<credentials>@",
            uri,
        )


settings = Settings()
