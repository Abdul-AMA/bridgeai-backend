from fastapi import APIRouter

from .analytics import router as analytics_router
from .logs import router as logs_router
from .overview import router as overview_router
from .teams import router as teams_router
from .users import router as users_router

router = APIRouter()
router.include_router(overview_router)
router.include_router(users_router)
router.include_router(teams_router)
router.include_router(analytics_router)
router.include_router(logs_router)
