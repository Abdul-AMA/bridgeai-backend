import math
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.admin.deps import verify_super_admin
from app.db.session import get_db
from app.models.user import User
from app.repositories.admin_repository import AdminRepository
from app.schemas.admin import (
    AdminAuditLogOut,
    AdminErrorLogOut,
    AdminLogEntryOut,
    AdminLogPageOut,
    PaginatedResponse,
)

router = APIRouter()

VALID_CATEGORIES = {
    "user_activity",
    "ai_generation",
    "auth",
    "api_errors",
    "audit_trail",
    "token_usage",
    "system",
}


@router.get("/logs", response_model=AdminLogPageOut)
def get_logs(
    category: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    actor: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(verify_super_admin),
):
    from fastapi import HTTPException, status

    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"category must be one of: {', '.join(sorted(VALID_CATEGORIES))}",
        )

    repo = AdminRepository(db)
    items, total = repo.get_logs_paginated(
        category=category,
        page=page,
        page_size=page_size,
        from_date=from_date,
        to_date=to_date,
        actor=actor,
        keyword=keyword,
    )
    pages = max(1, math.ceil(total / page_size))
    return {
        "category": category,
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.get("/audit", response_model=PaginatedResponse[AdminAuditLogOut])
def get_audit(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    actor: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(verify_super_admin),
):
    repo = AdminRepository(db)
    items, total = repo.get_audit_logs_paginated(
        page=page,
        page_size=page_size,
        from_date=from_date,
        to_date=to_date,
        actor=actor,
    )
    pages = max(1, math.ceil(total / page_size))
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/errors", response_model=PaginatedResponse[AdminErrorLogOut])
def get_errors(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(verify_super_admin),
):
    repo = AdminRepository(db)
    rows, total = repo.get_error_logs_paginated(
        page=page,
        page_size=page_size,
        from_date=from_date,
        to_date=to_date,
        keyword=keyword,
    )
    pages = max(1, math.ceil(total / page_size))
    return {"items": rows, "total": total, "page": page, "page_size": page_size, "pages": pages}
