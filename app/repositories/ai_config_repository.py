"""
AI Configuration Repository for database operations.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.base_repository import BaseRepository
from app.models.user_ai_config import UserAIConfig


class AIConfigRepository(BaseRepository[UserAIConfig]):
    """Repository for UserAIConfig model operations."""

    def __init__(self, db: Session):
        """
        Initialize AIConfigRepository.

        Args:
            db: Database session
        """
        super().__init__(UserAIConfig, db)

    def get_by_user_id(self, user_id: int) -> Optional[UserAIConfig]:
        """
        Get AI config by user ID.

        Args:
            user_id: User ID

        Returns:
            UserAIConfig or None if not found
        """
        return (
            self.db.query(UserAIConfig).filter(UserAIConfig.user_id == user_id).first()
        )

    def get_active_by_user_id(self, user_id: int) -> Optional[UserAIConfig]:
        """
        Get active AI config by user ID.

        Args:
            user_id: User ID

        Returns:
            Active UserAIConfig or None if not found
        """
        return (
            self.db.query(UserAIConfig)
            .filter(UserAIConfig.user_id == user_id, UserAIConfig.is_active == True)
            .first()
        )

    def delete_by_user_id(self, user_id: int) -> bool:
        """
        Delete AI config by user ID.

        Args:
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        config = self.get_by_user_id(user_id)
        if config:
            self.delete(config)
            return True
        return False
