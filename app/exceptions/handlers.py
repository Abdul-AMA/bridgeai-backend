"""Exception handlers for converting domain exceptions to HTTP responses."""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.exceptions.base import (
    BridgeAIException,
    NotFoundException,
    ForbiddenException,
    ValidationException,
    ConflictException,
)


async def bridgeai_exception_handler(request: Request, exc: BridgeAIException) -> JSONResponse:
    """Handle all BridgeAI domain exceptions."""
    # Map exception types to HTTP status codes
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    if isinstance(exc, NotFoundException):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ForbiddenException):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, ValidationException):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, ConflictException):
        status_code = status.HTTP_409_CONFLICT
    
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message},
    )
