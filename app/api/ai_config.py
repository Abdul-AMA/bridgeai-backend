"""
AI Configuration API endpoints.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.ai_config import (
    AIConfigCreate,
    AIConfigOut,
    AIConfigUpdate,
    AIProviderEnum,
    ProviderInfo,
    ProvidersListOut,
    PROVIDER_MODELS,
)
from app.services.ai_config_service import AIConfigService

router = APIRouter()


@router.get("", response_model=AIConfigOut | None)
def get_ai_config(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get current user's AI configuration.
    Returns None if no configuration exists.
    API key is never returned in the response.
    """
    config = AIConfigService.get_config(db, current_user.id)
    if not config:
        return None

    return AIConfigOut(
        provider=AIProviderEnum(config.provider.value),
        model_id=config.model_id,
        is_active=config.is_active,
        created_at=config.created_at,
    )


@router.put("", response_model=AIConfigOut)
def save_ai_config(
    data: AIConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create or update user's AI configuration.
    The API key will be encrypted before storage.
    """
    config = AIConfigService.save_config(db, current_user.id, data)

    return AIConfigOut(
        provider=AIProviderEnum(config.provider.value),
        model_id=config.model_id,
        is_active=config.is_active,
        created_at=config.created_at,
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_ai_config(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Delete user's AI configuration.
    Falls back to server default after deletion.
    """
    AIConfigService.delete_config(db, current_user.id)


@router.get("/providers", response_model=ProvidersListOut)
def list_providers():
    """
    List all supported AI providers and their available models.
    """
    providers = [
        ProviderInfo(provider=provider, models=models)
        for provider, models in PROVIDER_MODELS.items()
    ]
    return ProvidersListOut(providers=providers)


@router.patch("", response_model=AIConfigOut)
def update_ai_config(
    data: AIConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update user's AI configuration.
    Only provided fields will be updated.
    """
    config = AIConfigService.update_config(db, current_user.id, data)

    return AIConfigOut(
        provider=AIProviderEnum(config.provider.value),
        model_id=config.model_id,
        is_active=config.is_active,
        created_at=config.created_at,
    )
