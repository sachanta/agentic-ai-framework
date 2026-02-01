"""
Settings model for database storage.
"""
from datetime import datetime
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field


class SettingsModel(BaseModel):
    """Settings document model for MongoDB."""

    id: Optional[str] = Field(default=None, alias="_id")
    category: str  # general, api, llm, security, etc.
    settings: Dict[str, Any] = {}
    updated_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# Default settings structure
DEFAULT_SETTINGS = {
    "general": {
        "appName": "Agentic AI Framework",
        "logLevel": "info",
        "timezone": "UTC",
        "maxConcurrentTasks": 10,
    },
    "api": {
        "rateLimit": 100,
        "rateLimitWindow": 60,  # seconds
        "timeout": 30000,  # ms
        "maxRequestSize": "10mb",
    },
    "llm": {
        "defaultProvider": "openai",
        "defaultModel": "gpt-4",
        "temperature": 0.7,
        "maxTokens": 4096,
        "providers": {
            "openai": {
                "enabled": True,
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            },
            "ollama": {
                "enabled": True,
                "models": ["llama2", "mistral", "codellama"],
            },
            "bedrock": {
                "enabled": False,
                "models": ["anthropic.claude-v2", "amazon.titan-text-express-v1"],
            },
        },
    },
    "security": {
        "sessionTimeout": 1440,  # minutes (24 hours)
        "maxLoginAttempts": 5,
        "lockoutDuration": 15,  # minutes
        "requireMFA": False,
    },
    "notifications": {
        "emailEnabled": False,
        "slackEnabled": False,
        "webhookEnabled": False,
    },
}
