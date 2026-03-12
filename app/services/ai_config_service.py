"""
AI Configuration Service - Business logic for user AI settings.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user_ai_config import UserAIConfig, AIProvider
from app.schemas.ai_config import (
    AIConfigCreate,
    AIConfigUpdate,
    AIProviderEnum,
    PROVIDER_MODELS,
)
from app.repositories.ai_config_repository import AIConfigRepository
from app.utils.encryption import encrypt_api_key, decrypt_api_key


class AIConfigService:
    """Service for managing user AI configuration."""

    @staticmethod
    def save_config(db: Session, user_id: int, data: AIConfigCreate) -> UserAIConfig:
        """
        Save (create or update) user AI config.
        Encrypts the API key before storing.

        Args:
            db: Database session
            user_id: User ID
            data: Configuration data

        Returns:
            Saved UserAIConfig
        """
        AIConfigService.validate_provider_model(data.provider, data.model_id)

        repo = AIConfigRepository(db)
        existing = repo.get_by_user_id(user_id)

        if existing:
            existing.provider = AIProvider[data.provider.value]
            existing.model_id = data.model_id
            if data.api_key:
                existing.api_key_encrypted = encrypt_api_key(data.api_key)
            config = repo.update(existing)
        else:
            config = UserAIConfig(
                user_id=user_id,
                provider=AIProvider[data.provider.value],
                model_id=data.model_id,
                api_key_encrypted=encrypt_api_key(data.api_key)
                if data.api_key
                else None,
                is_active=True,
            )
            config = repo.create(config)

        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def get_config(db: Session, user_id: int) -> Optional[UserAIConfig]:
        """
        Get user's AI config (without decrypting the key).

        Args:
            db: Database session
            user_id: User ID

        Returns:
            UserAIConfig or None
        """
        repo = AIConfigRepository(db)
        return repo.get_by_user_id(user_id)

    @staticmethod
    def get_decrypted_key(db: Session, user_id: int) -> Optional[str]:
        """
        Get decrypted API key for user.
        Only used internally by AI layer.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Decrypted API key or None
        """
        repo = AIConfigRepository(db)
        config = repo.get_active_by_user_id(user_id)

        if not config or not config.api_key_encrypted:
            return None

        return decrypt_api_key(config.api_key_encrypted)

    @staticmethod
    def update_config(db: Session, user_id: int, data: AIConfigUpdate) -> UserAIConfig:
        """
        Update user AI config.

        Args:
            db: Database session
            user_id: User ID
            data: Update data

        Returns:
            Updated UserAIConfig
        """
        repo = AIConfigRepository(db)
        config = repo.get_by_user_id(user_id)

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI configuration not found",
            )

        if data.provider is not None:
            config.provider = AIProvider[data.provider.value]
        if data.model_id is not None:
            if data.provider is not None:
                AIConfigService.validate_provider_model(data.provider, data.model_id)
            else:
                AIConfigService.validate_provider_model(
                    AIProviderEnum(config.provider.value), data.model_id
                )
            config.model_id = data.model_id
        if data.api_key is not None:
            config.api_key_encrypted = encrypt_api_key(data.api_key)
        if data.is_active is not None:
            config.is_active = data.is_active

        config = repo.update(config)
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def delete_config(db: Session, user_id: int) -> bool:
        """
        Delete user's AI config.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            True if deleted
        """
        repo = AIConfigRepository(db)
        deleted = repo.delete_by_user_id(user_id)
        if deleted:
            db.commit()
        return deleted

    @staticmethod
    def validate_provider_model(provider: AIProviderEnum, model_id: str) -> bool:
        """
        Validate that the model belongs to the provider.

        Args:
            provider: AI provider
            model_id: Model ID

        Returns:
            True if valid

        Raises:
            HTTPException: If model is not valid for provider
        """
        valid_models = PROVIDER_MODELS.get(provider, [])
        if model_id not in valid_models:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model '{model_id}' for provider '{provider.value}'. "
                f"Valid models: {', '.join(valid_models)}",
            )
        return True

    @staticmethod
    def get_provider_info() -> dict:
        """
        Get all supported providers and their models.

        Returns:
            Dictionary of providers and models
        """
        return PROVIDER_MODELS
