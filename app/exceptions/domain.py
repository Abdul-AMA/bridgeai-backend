"""Domain-specific exceptions for BridgeAI entities."""

from .base import NotFoundException, ForbiddenException, ValidationException, ConflictException


# Resource Not Found Exceptions
class ProjectNotFoundException(NotFoundException):
    """Raised when a project is not found."""

    def __init__(self, project_id: int = None):
        identifier = str(project_id) if project_id else ""
        super().__init__("Project", identifier)


class TeamNotFoundException(NotFoundException):
    """Raised when a team is not found."""

    def __init__(self, team_id: int = None):
        identifier = str(team_id) if team_id else ""
        super().__init__("Team", identifier)


class SessionNotFoundException(NotFoundException):
    """Raised when a session is not found."""

    def __init__(self, session_id: int = None):
        identifier = str(session_id) if session_id else ""
        super().__init__("Session", identifier)


class CRSNotFoundException(NotFoundException):
    """Raised when a CRS document is not found."""

    def __init__(self, crs_id: int = None):
        identifier = str(crs_id) if crs_id else ""
        super().__init__("CRS document", identifier)


class InvitationNotFoundException(NotFoundException):
    """Raised when an invitation is not found."""

    def __init__(self, invitation_id: int = None):
        identifier = str(invitation_id) if invitation_id else ""
        super().__init__("Invitation", identifier)


class MemberNotFoundException(NotFoundException):
    """Raised when a team member is not found."""

    def __init__(self, member_id: int = None):
        identifier = str(member_id) if member_id else ""
        super().__init__("Team member", identifier)


class NotificationNotFoundException(NotFoundException):
    """Raised when a notification is not found."""

    def __init__(self, notification_id: int = None):
        identifier = str(notification_id) if notification_id else ""
        super().__init__("Notification", identifier)


# Permission Exceptions
class PermissionDeniedException(ForbiddenException):
    """Raised when user lacks required permissions."""

    def __init__(self, action: str = None):
        message = "You do not have permission"
        if action:
            message += f" to {action}"
        super().__init__(message)


# Validation and Business Logic Exceptions
class InvalidInvitationException(ValidationException):
    """Raised when invitation is invalid (expired, already used, etc.)."""

    def __init__(self, reason: str = "Invitation is not valid"):
        super().__init__(reason)


class CRSStatusException(ConflictException):
    """Raised when CRS operation conflicts with current status."""

    def __init__(self, message: str = "Cannot perform operation due to CRS status"):
        super().__init__(message)
