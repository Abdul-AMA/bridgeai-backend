"""Tests for email utility functions."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import smtplib

from app.utils.email import (
    send_email,
    send_invitation_email,
)


class TestInvitationEmail:
    """Tests for send_invitation_email function."""

    @patch("app.utils.email.send_email")
    def test_send_invitation_email_with_inviter(self, mock_send):
        """Test invitation email with inviter name."""
        send_invitation_email(
            to_email="newuser@example.com",
            invite_link="https://example.com/invite/abc123",
            team_name="Development Team",
            inviter_name="John Doe",
        )
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        
        # Args are positional: (to_email, subject, html_content, text_content)
        assert call_args[0][0] == "newuser@example.com"  # to_email
        assert "Development Team" in call_args[0][1]  # subject
        assert "John Doe" in call_args[0][2]  # html_content
        assert "https://example.com/invite/abc123" in call_args[0][2]

    @patch("app.utils.email.send_email")
    def test_send_invitation_email_without_inviter(self, mock_send):
        """Test invitation email without inviter name."""
        send_invitation_email(
            to_email="newuser@example.com",
            invite_link="https://example.com/invite/xyz789",
            team_name="Marketing Team",
        )
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        
        assert "Marketing Team" in call_args[0][2]  # html_content
        assert "https://example.com/invite/xyz789" in call_args[0][2]

    @patch("app.utils.email.send_email")
    def test_invitation_email_includes_branding(self, mock_send):
        """Test invitation email includes BridgeAI branding."""
        send_invitation_email(
            to_email="test@example.com",
            invite_link="https://example.com/invite/123",
            team_name="Test Team",
        )
        
        call_args = mock_send.call_args[0]
        html = call_args[2]
        
        assert "BridgeAI" in html
        assert "Accept Invitation" in html

