"""Base exception classes for the application."""


class BridgeAIException(Exception):
    """Base exception for all BridgeAI domain exceptions."""

    def __init__(self, message: str = "An error occurred"):
        self.message = message
        super().__init__(self.message)


class NotFoundException(BridgeAIException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str = "Resource", identifier: str = ""):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message)


class ForbiddenException(BridgeAIException):
    """Raised when user lacks permission to perform an action."""

    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(message)


class ValidationException(BridgeAIException):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message)


class ConflictException(BridgeAIException):
    """Raised when operation conflicts with current state."""

    def __init__(self, message: str = "Operation conflicts with current state"):
        super().__init__(message)
