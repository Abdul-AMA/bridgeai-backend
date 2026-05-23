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
    AdminChangeRoleRequest,
    AdminSuspendRequest,
    AdminUserDetailOut,
    AdminUserListItemOut,
    AdminUserRoleOut,
    AdminUserStatusOut,
    PaginatedResponse,
)
from app.services import admin_service

router = APIRouter()


@router.get("/users", response_model=PaginatedResponse[AdminUserListItemOut])
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    team_id: Optional[int] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(verify_super_admin),
):
    repo = AdminRepository(db)
    items, total = repo.get_users_paginated(
        page=page,
        page_size=page_size,
        role=role,
        status=status,
        team_id=team_id,
        from_date=from_date,
        to_date=to_date,
        search=search,
    )
    pages = max(1, math.ceil(total / page_size))
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/users/{user_id}", response_model=AdminUserDetailOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(verify_super_admin),
):
    repo = AdminRepository(db)
    user = repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/users/{user_id}/status", response_model=AdminUserStatusOut)
def update_user_status(
    user_id: int,
    body: AdminSuspendRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(verify_super_admin),
):
    if body.action == "suspend":
        if not body.reason:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="reason is required when suspending a user",
            )
        return admin_service.suspend_user(db, actor, user_id, body.reason)
    else:
        return admin_service.reactivate_user(db, actor, user_id)


@router.patch("/users/{user_id}/role", response_model=AdminUserRoleOut)
def update_user_role(
    user_id: int,
    body: AdminChangeRoleRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(verify_super_admin),
):
    updated = admin_service.change_user_role(db, actor, user_id, body.role)
    return {"id": updated.id, "role": updated.role.value, "updated_at": updated.created_at}
