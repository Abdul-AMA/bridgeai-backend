"""
Chats API Module.
Aggregates all chat endpoint routers for backward compatibility.
"""
from fastapi import APIRouter

from .sessions import router as sessions_router
from .websocket import router as websocket_router, manager

# Create main router that includes all sub-routers
router = APIRouter()

# Include all chat sub-routers
router.include_router(sessions_router, tags=["Chats"])
router.include_router(websocket_router, tags=["Chats WebSocket"])

# Export manager for backward compatibility
__all__ = ["router", "manager"]
