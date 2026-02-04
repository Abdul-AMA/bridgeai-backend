"""Repository for CRS audit log operations."""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.audit import CRSAuditLog
from app.repositories.base_repository import BaseRepository


class AuditLogRepository(BaseRepository[CRSAuditLog]):
    """Repository for CRSAuditLog database operations."""

    def __init__(self, db: Session):
        """Initialize AuditLogRepository."""
        super().__init__(CRSAuditLog, db)

    def get_by_crs(
        self,
        crs_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[CRSAuditLog]:
        """
        Get audit logs for a CRS document.

        Args:
            crs_id: CRS document ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of audit logs ordered by changed_at DESC
        """
        return (
            self.db.query(CRSAuditLog)
            .filter(CRSAuditLog.crs_id == crs_id)
            .order_by(CRSAuditLog.changed_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_log(
        self,
        crs_id: int,
        changed_by: int,
        action: str,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        old_content: Optional[str] = None,
        new_content: Optional[str] = None,
        summary: Optional[str] = None
    ) -> CRSAuditLog:
        """
        Create an audit log entry.

        Args:
            crs_id: CRS document ID
            changed_by: User ID who made the change
            action: Action performed
            old_status: Previous status
            new_status: New status
            old_content: Previous content
            new_content: New content
            summary: Change summary

        Returns:
            Created audit log
        """
        audit_log = CRSAuditLog(
            crs_id=crs_id,
            changed_by=changed_by,
            action=action,
            old_status=old_status,
            new_status=new_status,
            old_content=old_content,
            new_content=new_content,
            summary=summary
        )
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        return audit_log
