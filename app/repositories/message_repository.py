"""Repository for message operations."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.message import Message
from app.repositories.base_repository import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Repository for Message database operations."""

    def __init__(self, db: Session):
        """Initialize MessageRepository."""
        super().__init__(Message, db)

    def get_by_session(
        self,
        session_id: int,
        skip: int = 0,
        limit: int = 100,
        order_desc: bool = False
    ) -> List[Message]:
        """
        Get messages for a session.

        Args:
            session_id: Session ID
            skip: Number of records to skip
            limit: Maximum number of records
            order_desc: Order by created_at descending

        Returns:
            List of messages
        """
        query = self.db.query(Message).filter(Message.session_id == session_id)

        if order_desc:
            query = query.order_by(Message.created_at.desc())
        else:
            query = query.order_by(Message.created_at.asc())

        return query.offset(skip).limit(limit).all()

    def get_session_message_count(self, session_id: int) -> int:
        """
        Count messages in a session.

        Args:
            session_id: Session ID

        Returns:
            Message count
        """
        return self.db.query(Message).filter(Message.session_id == session_id).count()

    def delete_by_session(self, session_id: int) -> int:
        """
        Delete all messages in a session.

        Args:
            session_id: Session ID

        Returns:
            Number of deleted messages
        """
        deleted = self.db.query(Message).filter(Message.session_id == session_id).delete()
        self.db.commit()
        return deleted

    def get_latest_by_session(self, session_id: int, limit: int = 10) -> List[Message]:
        """
        Get latest messages from a session.

        Args:
            session_id: Session ID
            limit: Maximum number of messages

        Returns:
            List of latest messages
        """
        return (
            self.db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
