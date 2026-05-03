"""
AI Configuration schemas for user API key management.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.user_ai_config import AIProvider


class AIProviderEnum(str, Enum):
    anthropic = "anthropic"
    openai = "openai"
    gemini = "gemini"
    groq = "groq"
    mistral = "mistral"


PROVIDER_MODELS: Dict[AIProviderEnum, List[str]] = {
    AIProviderEnum.anthropic: [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3-haiku-20240307",
        "claude-3-opus-20240229",
    ],
    AIProviderEnum.openai: [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
    ],
    AIProviderEnum.gemini: [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
    ],
    AIProviderEnum.groq: [
        "llama-3.1-70b-versatile",
        "llama-3.1-405b-reasoning",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ],
    AIProviderEnum.mistral: [
        "mistral-large-latest",
        "mistral-small-latest",
        "mistral-medium-latest",
    ],
}


class AIConfigCreate(BaseModel):
    """Schema for creating a new AI configuration."""

    provider: AIProviderEnum = Field(..., description="AI provider")
    model_id: str = Field(..., description="Model ID for the selected provider")
    api_key: str = Field(
        ..., min_length=1, description="API key for the provider (write-only)"
    )


class AIConfigUpdate(BaseModel):
    """Schema for updating an existing AI configuration."""

    provider: Optional[AIProviderEnum] = Field(None, description="AI provider")
    model_id: Optional[str] = Field(
        None, description="Model ID for the selected provider"
    )
    api_key: Optional[str] = Field(
        None, min_length=1, description="API key for the provider (write-only)"
    )
    is_active: Optional[bool] = Field(None, description="Whether this config is active")


class AIConfigOut(BaseModel):
    """Schema for returning AI configuration (never includes API key)."""

    provider: AIProviderEnum
    model_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProviderInfo(BaseModel):
    """Schema for provider information."""

    provider: AIProviderEnum
    models: List[str]


class ProvidersListOut(BaseModel):
    """Schema for listing all supported providers and models."""

    providers: List[ProviderInfo]
