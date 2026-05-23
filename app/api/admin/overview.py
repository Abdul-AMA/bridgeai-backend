from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.admin.deps import verify_super_admin
from app.db.session import get_db
from app.models.user import User
from app.repositories.admin_repository import AdminRepository
from app.schemas.admin import AdminOverviewStatsOut

router = APIRouter()


@router.get("/overview", response_model=AdminOverviewStatsOut)
def get_admin_overview(
    db: Session = Depends(get_db),
    _: User = Depends(verify_super_admin),
):
    repo = AdminRepository(db)
    return repo.get_overview_stats()
