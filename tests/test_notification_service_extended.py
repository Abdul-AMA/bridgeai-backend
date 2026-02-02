"""Additional tests for notification service - email sending and error handling."""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.models.crs import CRSDocument, CRSStatus, CRSPattern
from app.models.notification import Notification
from app.models.project import Project
from app.models.user import User
from app.services.notification_service import (
    notify_crs_created,
    notify_crs_approved,
    notify_crs_rejected,
    notify_crs_updated,
    send_crs_notification_email,
)


class TestNotificationServiceWithEmail:
    """Test notification service with email sending enabled."""

    @patch("app.services.notification_service.send_email")
    def test_notify_crs_created_with_email(
        self, mock_send_email, db: Session, client_user, sample_project
    ):
        """Test CRS created notification with email sending."""
        crs = CRSDocument(
            project_id=sample_project.id,
            status=CRSStatus.draft,
            pattern=CRSPattern.ieee_830,
            version=1,
            edit_version=1,
            content="# Test CRS",
            created_by=client_user.id,
        )
        db.add(crs)
        db.commit()
        db.refresh(crs)

        notify_crs_created(
            db=db,
            crs=crs,
            project=sample_project,
            notify_users=[client_user.id],
            send_email_notification=True,  # Email enabled
        )

        # Verify email was sent
        mock_send_email.assert_called_once()
        # Args are: (to_email, subject, html_content, text_content)
        call_args = mock_send_email.call_args[0]
        assert client_user.email == call_args[0]  # to_email
        assert sample_project.name in call_args[1]  # subject

    @patch("app.services.notification_service.send_email")
    def test_notify_crs_approved_with_email(
        self, mock_send_email, db: Session, client_user, sample_project
    ):
        """Test CRS approved notification with email."""
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
            send_email_notification=True,
        )

        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[0]
        assert "approved" in call_args[1].lower()  # subject

    @patch("app.services.notification_service.send_email")
    def test_notify_crs_rejected_with_email(
        self, mock_send_email, db: Session, client_user, sample_project
    ):
        """Test CRS rejected notification with email."""
        crs = CRSDocument(
            project_id=sample_project.id,
            status=CRSStatus.rejected,
            pattern=CRSPattern.agile_user_stories,
            version=1,
            edit_version=1,
            content="# Rejected CRS",
            created_by=client_user.id,
            rejection_reason="Insufficient detail",
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
            send_email_notification=True,
        )

        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[0]
        assert "rejected" in call_args[1].lower()  # subject
        # The rejection reason is stored in CRS but not included in email
        # Just verify the email mentions rejection
        assert "rejected" in call_args[2].lower()  # html_content

    @patch("app.services.notification_service.send_email")
    def test_notify_multiple_users_with_email(
        self, mock_send_email, db: Session, client_user, sample_project
    ):
        """Test notifying multiple users sends multiple emails."""
        from app.models.user import UserRole
        from app.utils.hash import hash_password

        # Create additional users
        user2 = User(
            full_name="User 2",
            email="user2@test.com",
            password_hash=hash_password("TestPassword123!"),
            role=UserRole.client,
        )
        user3 = User(
            full_name="User 3",
            email="user3@test.com",
            password_hash=hash_password("TestPassword123!"),
            role=UserRole.ba,
        )
        db.add_all([user2, user3])
        db.commit()
        db.refresh(user2)
        db.refresh(user3)

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

        notify_crs_created(
            db=db,
            crs=crs,
            project=sample_project,
            notify_users=[client_user.id, user2.id, user3.id],
            send_email_notification=True,
        )

        # Verify 3 emails were sent
        assert mock_send_email.call_count == 3

    def test_send_crs_notification_email_structure(self):
        """Test CRS notification email HTML structure."""
        with patch("app.services.notification_service.send_email") as mock_send:
            send_crs_notification_email(
                to_email="test@example.com",
                subject="Test Subject",
                event_type="CRS Created",
                crs_id=42,
                project_name="Test Project",
                details="Test details",
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]

            # Check email structure (positional: to_email, subject, html_content, text_content)
            assert call_args[0] == "test@example.com"  # to_email
            assert call_args[1] == "Test Subject"  # subject
            assert "Test Project" in call_args[2]  # html_content
            assert "#42" in call_args[2]  # html_content
            assert "CRS Created" in call_args[2]  # html_content
            assert "BridgeAI" in call_args[2]  # html_content
            assert call_args[3] is not None  # text_content


class TestNotificationServiceErrorHandling:
    """Test notification service error handling."""

    def test_notify_user_not_found(self, db: Session, client_user, sample_project):
        """Test notification when user doesn't exist."""
        crs = CRSDocument(
            project_id=sample_project.id,
            status=CRSStatus.draft,
            pattern=CRSPattern.babok,
            version=1,
            edit_version=1,
            content="# Test",
            created_by=client_user.id,
        )
        db.add(crs)
        db.commit()

        # Try to notify non-existent user (ID 99999)
        notify_crs_created(
            db=db,
            crs=crs,
            project=sample_project,
            notify_users=[99999],
            send_email_notification=False,
        )

        # Should not crash, just skip the user
        notifications = db.query(Notification).all()
        assert len(notifications) == 0

    @patch("app.services.notification_service.send_email")
    def test_email_sending_failure_doesnt_break_notification(
        self, mock_send_email, db: Session, client_user, sample_project
    ):
        """Test that email sending failures don't prevent notification creation."""
        mock_send_email.side_effect = Exception("SMTP error")

        crs = CRSDocument(
            project_id=sample_project.id,
            status=CRSStatus.draft,
            pattern=CRSPattern.ieee_830,
            version=1,
            edit_version=1,
            content="# Test",
            created_by=client_user.id,
        )
        db.add(crs)
        db.commit()

        # Should not crash even if email fails
        try:
            notify_crs_created(
                db=db,
                crs=crs,
                project=sample_project,
                notify_users=[client_user.id],
                send_email_notification=True,
            )
        except Exception:
            pass  # Email failure is acceptable

        # In-app notification should still be created
        notifications = db.query(Notification).filter(
            Notification.user_id == client_user.id
        ).all()
        assert len(notifications) > 0

    def test_notification_with_empty_user_list(
        self, db: Session, client_user, sample_project
    ):
        """Test notification with empty user list."""
        crs = CRSDocument(
            project_id=sample_project.id,
            status=CRSStatus.draft,
            pattern=CRSPattern.babok,
            version=1,
            edit_version=1,
            content="# Test",
            created_by=client_user.id,
        )
        db.add(crs)
        db.commit()

        # Empty user list should not crash
        notify_crs_created(
            db=db,
            crs=crs,
            project=sample_project,
            notify_users=[],
            send_email_notification=False,
        )

        notifications = db.query(Notification).all()
        assert len(notifications) == 0

    def test_notification_with_duplicate_users(
        self, db: Session, client_user, sample_project
    ):
        """Test notification handles duplicate user IDs."""
        crs = CRSDocument(
            project_id=sample_project.id,
            status=CRSStatus.draft,
            pattern=CRSPattern.babok,
            version=1,
            edit_version=1,
            content="# Test",
            created_by=client_user.id,
        )
        db.add(crs)
        db.commit()

        # Duplicate user in list
        notify_crs_created(
            db=db,
            crs=crs,
            project=sample_project,
            notify_users=[client_user.id, client_user.id, client_user.id],
            send_email_notification=False,
        )

        # Should create notifications (may be 1 or 3 depending on implementation)
        notifications = db.query(Notification).filter(
            Notification.user_id == client_user.id
        ).all()
        assert len(notifications) >= 1

    @patch("app.services.notification_service.send_email")
    def test_updated_notification_with_version_info(
        self, mock_send_email, db: Session, client_user, sample_project
    ):
        """Test CRS updated notification includes version information."""
        crs = CRSDocument(
            project_id=sample_project.id,
            status=CRSStatus.draft,
            pattern=CRSPattern.ieee_830,
            version=2,
            edit_version=5,
            content="# Updated CRS",
            created_by=client_user.id,
        )
        db.add(crs)
        db.commit()

        notify_crs_updated(
            db=db,
            crs=crs,
            project=sample_project,
            notify_users=[client_user.id],
            send_email_notification=True,
        )

        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args[0]  # Positional args
        
        # Should mention version (html_content is at index 2)
        html = call_args[2]
        assert "version" in html.lower() or str(crs.version) in html
