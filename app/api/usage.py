from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.usage import AIUsageHistoryResponse, AIUsageSummaryResponse
from app.services import usage_service

router = APIRouter()


@router.get("/me/summary", response_model=AIUsageSummaryResponse)
def get_my_usage_summary(
    days: int = Query(30, ge=1, le=365, description="Number of past days to include"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return aggregated AI token usage statistics for the current user."""
    return usage_service.get_user_summary(db, current_user.id, days=days)


@router.get("/me/history", response_model=AIUsageHistoryResponse)
def get_my_usage_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a paginated history of individual AI calls for the current user."""
    return usage_service.get_user_history(db, current_user.id, page=page, limit=limit)
