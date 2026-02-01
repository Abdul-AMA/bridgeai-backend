"""Tests for notification service functionality."""
import pytest
from sqlalchemy.orm import Session

from app.models.crs import CRSDocument, CRSStatus, CRSPattern
from app.models.notification import Notification, NotificationType
from app.models.project import Project, ProjectStatus  
from app.models.team import Team
from app.models.user import User
from app.services.notification_service import (
    create_notification,
    notify_crs_approved,
    notify_crs_comment_added,
    notify_crs_created,
    notify_crs_rejected,
    notify_crs_status_changed,
    notify_crs_updated,
)


class TestNotificationService:
    """Test notification service functions."""

    def test_create_notification(self, db: Session, client_user):
        """Test creating a notification."""
        notification = create_notification(
            db=db,
            user_id=client_user.id,
            title="Test Title",
            message="Test message",
            notification_type=NotificationType.PROJECT_APPROVAL,
            reference_id=1,
        )

        assert notification.id is not None
        assert notification.user_id == client_user.id
        assert notification.title == "Test Title"
        assert notification.message == "Test message"
        assert notification.type == NotificationType.PROJECT_APPROVAL
        assert notification.reference_id == 1
        assert notification.is_read is False

    def test_notify_crs_created(self, db: Session, client_user, sample_project):
        """Test CRS created notification."""
        # Create a CRS document
        crs = CRSDocument(
            project_id=sample_project.id,
            status=CRSStatus.draft,
            pattern=CRSPattern.babok,
            version=1,
            edit_version=1,
            content="# Test CRS",
            created_by=client_user.id,
        )
        db.add(crs)
        db.commit()
        db.refresh(crs)

        # Notify about CRS creation
        notify_crs_created(
            db=db,
            crs=crs,
            project=sample_project,
            notify_users=[client_user.id],
            send_email_notification=False,
        )

        # Check notification was created
        notifications = (
            db.query(Notification)
            .filter(Notification.type == NotificationType.CRS_CREATED)
            .all()
        )
        assert len(notifications) > 0
        assert notifications[0].reference_id == crs.id

    def test_notify_crs_updated(self, db: Session, client_user, sample_project):
        """Test CRS updated notification."""
        crs = CRSDocument(
            project_id=sample_project.id,
            status=CRSStatus.draft,
            pattern=CRSPattern.babok,
            version=1,
            edit_version=2,
            content="# Updated CRS",
            created_by=client_user.id,
        )
        db.add(crs)
        db.commit()
        db.refresh(crs)

        notify_crs_updated(
            db=db,
            crs=crs,
            project=sample_project,
            notify_users=[client_user.id],
            send_email_notification=False,
        )

        notifications = (
            db.query(Notification)
            .filter(Notification.type == NotificationType.CRS_UPDATED)
            .all()
        )
        assert len(notifications) > 0

    def test_notify_crs_approved(self, db: Session, client_user, sample_project):
        """Test CRS approved notification."""
        crs = CRSDocument(
            project_id=sample_project.id,
            status=CRSStatus.approved,
            pattern=CRSPattern.babok,
            version=1,
            edit_version=1,
            content="# Approved CRS",
            created_by=client_user.id,
            approved_by=client_user.id,
        )
        db.add(crs)
        db.commit()
        db.refresh(crs)

        notify_crs_approved(
            db=db,
            crs=crs,
            project=sample_project,
            approver=client_user,
            notify_users=[client_user.id],
            send_email_notification=False,
        )

        notifications = (
            db.query(Notification)
            .filter(Notification.type == NotificationType.CRS_APPROVED)
            .all()
        )
        assert len(notifications) > 0

    def test_notify_crs_rejected(self, db: Session, client_user, sample_project):
        """Test CRS rejected notification."""
        crs = CRSDocument(
            project_id=sample_project.id,
            status=CRSStatus.rejected,
            pattern=CRSPattern.babok,
            version=1,
            edit_version=1,
            content="# Rejected CRS",
            created_by=client_user.id,
            rejection_reason="Needs more detail",
        )
        db.add(crs)
        db.commit()
        db.refresh(crs)

        notify_crs_rejected(
            db=db,
            crs=crs,
            project=sample_project,
            rejector=client_user,
            notify_users=[client_user.id],
            send_email_notification=False,
        )

        notifications = (
            db.query(Notification)
            .filter(Notification.type == NotificationType.CRS_REJECTED)
            .all()
        )
        assert len(notifications) > 0

    def test_notification_persistence(self, db: Session, client_user):
        """Test that notifications are persisted correctly."""
        # Create multiple notifications
        for i in range(5):
            create_notification(
                db=db,
                user_id=client_user.id,
                title=f"Test {i}",
                message=f"Message {i}",
                notification_type=NotificationType.PROJECT_APPROVAL,
                reference_id=i,
            )

        # Check all are saved
        notifications = (
            db.query(Notification)
            .filter(Notification.user_id == client_user.id)
            .all()
        )
        assert len(notifications) >= 5

    def test_notify_crs_status_changed(self, db: Session, client_user, sample_project):
        """Test CRS status changed notification."""
        crs = CRSDocument(
            project_id=sample_project.id,
            status=CRSStatus.under_review,
            pattern=CRSPattern.ieee_830,
            version=1,
            edit_version=1,
            content="# CRS Under Review",
            created_by=client_user.id,
        )
        db.add(crs)
        db.commit()
        db.refresh(crs)

        notify_crs_status_changed(
            db=db,
            crs=crs,
            project=sample_project,
            old_status="draft",
            new_status="under_review",
            notify_users=[client_user.id],
            send_email_notification=False,
        )

        notifications = (
            db.query(Notification)
            .filter(Notification.type == NotificationType.CRS_STATUS_CHANGED)
            .all()
        )
        assert len(notifications) > 0
        assert "under_review" in notifications[0].message.lower()

    def test_notify_crs_comment_added(self, db: Session, client_user, ba_user, sample_project):
        """Test CRS comment added notification."""
        from app.services.notification_service import notify_crs_comment_added
        
        crs = CRSDocument(
            project_id=sample_project.id,
            status=CRSStatus.draft,
            pattern=CRSPattern.babok,
            version=1,
            edit_version=1,
            content="# Test CRS",
            created_by=client_user.id,
        )
        db.add(crs)
        db.commit()
        db.refresh(crs)

        # Notify ba_user when client_user adds a comment
        notify_crs_comment_added(
            db=db,
            crs=crs,
            project=sample_project,
            comment_author=client_user,
            notify_users=[ba_user.id],  # Notify different user
            send_email_notification=False,
        )

        notifications = (
            db.query(Notification)
            .filter(Notification.type == NotificationType.CRS_COMMENT_ADDED)
            .all()
        )
        assert len(notifications) > 0
        assert client_user.full_name in notifications[0].message

    def test_notify_crs_review_assignment(self, db: Session, client_user, sample_project):
        """Test CRS review assignment notification."""
        from app.services.notification_service import notify_crs_review_assignment
        
        crs = CRSDocument(
            project_id=sample_project.id,
            status=CRSStatus.under_review,
            pattern=CRSPattern.agile_user_stories,
            version=1,
            edit_version=1,
            content="# CRS for Review",
            created_by=client_user.id,
        )
        db.add(crs)
        db.commit()
        db.refresh(crs)

        notify_crs_review_assignment(
            db=db,
            crs=crs,
            project=sample_project,
            reviewer_id=client_user.id,
            send_email_notification=False,
        )

        notifications = (
            db.query(Notification)
            .filter(Notification.type == NotificationType.CRS_REVIEW_ASSIGNED)
            .all()
        )
        assert len(notifications) > 0
        assert notifications[0].user_id == client_user.id

    def test_notification_with_metadata(self, db: Session, client_user):
        """Test creating notification with metadata."""
        meta_data = {
            "project_id": 123,
            "crs_version": 2,
            "additional_info": "test data"
        }
        
        notification = create_notification(
            db=db,
            user_id=client_user.id,
            title="Test with metadata",
            message="Test message",
            notification_type=NotificationType.CRS_CREATED,
            reference_id=1,
            meta_data=meta_data,
        )

        assert notification.meta_data is not None
        assert notification.meta_data["project_id"] == 123
        assert notification.meta_data["crs_version"] == 2

    def test_multiple_users_notification(self, db: Session, client_user, sample_project):
        """Test notifying multiple users."""
        # Create another user
        from app.utils.hash import hash_password
        from app.models.user import UserRole
        user2 = User(
            full_name="Test User 2",
            email="user2@example.com",
            password_hash=hash_password("TestPassword123!"),
            role=UserRole.client
        )
        db.add(user2)
        db.commit()
        db.refresh(user2)
        
        crs = CRSDocument(
            project_id=sample_project.id,
            status=CRSStatus.draft,
            pattern=CRSPattern.babok,
            version=1,
            edit_version=1,
            content="# Multi-user CRS",
            created_by=client_user.id,
        )
        db.add(crs)
        db.commit()
        db.refresh(crs)

        # Notify both users
        notify_crs_created(
            db=db,
            crs=crs,
            project=sample_project,
            notify_users=[client_user.id, user2.id],
            send_email_notification=False,
        )

        # Check both users received notifications
        user1_notifications = (
            db.query(Notification)
            .filter(
                Notification.user_id == client_user.id,
                Notification.type == NotificationType.CRS_CREATED,
                Notification.reference_id == crs.id
            )
            .all()
        )
        user2_notifications = (
            db.query(Notification)
            .filter(
                Notification.user_id == user2.id,
                Notification.type == NotificationType.CRS_CREATED,
                Notification.reference_id == crs.id
            )
            .all()
        )
        
        assert len(user1_notifications) > 0
        assert len(user2_notifications) > 0
