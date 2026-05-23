import math
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.admin.deps import verify_super_admin
from app.db.session import get_db
from app.models.user import User
from app.repositories.admin_repository import AdminRepository
from app.schemas.admin import (
    AdminSuspendRequest,
    AdminTeamDetailOut,
    AdminTeamListItemOut,
    AdminTeamStatusOut,
    PaginatedResponse,
)
from app.services import admin_service

router = APIRouter()


@router.get("/teams", response_model=PaginatedResponse[AdminTeamListItemOut])
def list_teams(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(verify_super_admin),
):
    repo = AdminRepository(db)
    items, total = repo.get_teams_paginated(
        page=page,
        page_size=page_size,
        status=status,
        from_date=from_date,
        to_date=to_date,
        search=search,
    )
    pages = max(1, math.ceil(total / page_size))
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/teams/{team_id}", response_model=AdminTeamDetailOut)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(verify_super_admin),
):
    repo = AdminRepository(db)
    team = repo.get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


@router.patch("/teams/{team_id}/status", response_model=AdminTeamStatusOut)
def update_team_status(
    team_id: int,
    body: AdminSuspendRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(verify_super_admin),
):
    if body.action == "suspend":
        if not body.reason:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="reason is required when suspending a team",
            )
        team = admin_service.suspend_team(db, actor, team_id, body.reason)
    else:
        team = admin_service.reactivate_team(db, actor, team_id)
    return {
        "id": team.id,
        "status": team.status.value,
        "suspended_by": team.suspended_by,
        "suspended_at": team.suspended_at,
        "suspension_reason": team.suspension_reason,
    }
