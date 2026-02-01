"""
Settings API schemas.
"""
from datetime import datetime
from typing import Dict, Optional, Any, List
from pydantic import BaseModel


class GeneralSettings(BaseModel):
    """General settings schema."""
    appName: str = "Agentic AI Framework"
    logLevel: str = "info"
    timezone: str = "UTC"
    maxConcurrentTasks: int = 10


class ApiSettings(BaseModel):
    """API settings schema."""
    rateLimit: int = 100
    rateLimitWindow: int = 60
    timeout: int = 30000
    maxRequestSize: str = "10mb"


class LLMProviderSettings(BaseModel):
    """LLM provider settings schema."""
    enabled: bool = True
    models: List[str] = []


class LLMSettings(BaseModel):
    """LLM settings schema."""
    defaultProvider: str = "openai"
    defaultModel: str = "gpt-4"
    temperature: float = 0.7
    maxTokens: int = 4096
    providers: Dict[str, LLMProviderSettings] = {}


class SecuritySettings(BaseModel):
    """Security settings schema."""
    sessionTimeout: int = 1440
    maxLoginAttempts: int = 5
    lockoutDuration: int = 15
    requireMFA: bool = False


class NotificationSettings(BaseModel):
    """Notification settings schema."""
    emailEnabled: bool = False
    slackEnabled: bool = False
    webhookEnabled: bool = False


class AllSettingsResponse(BaseModel):
    """All settings combined response."""
    general: GeneralSettings = GeneralSettings()
    api: ApiSettings = ApiSettings()
    llm: LLMSettings = LLMSettings()
    security: SecuritySettings = SecuritySettings()
    notifications: NotificationSettings = NotificationSettings()


class SettingsCategoryResponse(BaseModel):
    """Single category settings response."""
    category: str
    settings: Dict[str, Any]
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


class UpdateSettingsRequest(BaseModel):
    """Request to update settings."""
    settings: Dict[str, Any]
