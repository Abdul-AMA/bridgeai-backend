"""
Domain-specific exceptions for BridgeAI backend.
These provide semantic error handling across the application.
"""

from .base import (
    BridgeAIException,
    NotFoundException,
    ForbiddenException,
    ValidationException,
    ConflictException,
)
from .domain import (
    ProjectNotFoundException,
    TeamNotFoundException,
    SessionNotFoundException,
    CRSNotFoundException,
    InvitationNotFoundException,
    MemberNotFoundException,
    NotificationNotFoundException,
    InvalidInvitationException,
    CRSStatusException,
    PermissionDeniedException,
)

__all__ = [
    # Base exceptions
    "BridgeAIException",
    "NotFoundException",
    "ForbiddenException",
    "ValidationException",
    "ConflictException",
    # Domain exceptions
    "ProjectNotFoundException",
    "TeamNotFoundException",
    "SessionNotFoundException",
    "CRSNotFoundException",
    "InvitationNotFoundException",
    "MemberNotFoundException",
    "NotificationNotFoundException",
    "InvalidInvitationException",
    "CRSStatusException",
    "PermissionDeniedException",
]
