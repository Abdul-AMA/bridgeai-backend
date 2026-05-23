from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.admin.deps import verify_super_admin
from app.db.session import get_db
from app.models.user import User
from app.repositories.admin_repository import AdminRepository
from app.schemas.admin import AdminTimeSeriesOut

router = APIRouter()

VALID_METRICS = {"tokens", "crs_generations", "active_users", "new_teams", "ai_errors"}


@router.get("/analytics", response_model=AdminTimeSeriesOut)
def get_analytics(
    metric: str = Query(...),
    from_date: date = Query(...),
    to_date: date = Query(...),
    group_by: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(verify_super_admin),
):
    from fastapi import HTTPException, status

    if metric not in VALID_METRICS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"metric must be one of: {', '.join(sorted(VALID_METRICS))}",
        )

    repo = AdminRepository(db)
    return repo.get_analytics_timeseries(metric, from_date, to_date, group_by)
