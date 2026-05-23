"""Admin service — mutation operations for the super admin dashboard."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.admin_audit import AdminAuditLog
from app.models.team import Team, TeamStatus
from app.models.user import User, UserRole


def _write_audit_log(
    db: Session,
    actor: User,
    action: str,
    target_type: str,
    target_id: int,
    before_state: str | None,
    after_state: str | None,
    reason: str | None,
) -> None:
    log = AdminAuditLog(
        actor_id=actor.id,
        actor_email=actor.email,
        action=action,
        target_type=target_type,
        target_id=target_id,
        before_state=before_state,
        after_state=after_state,
        reason=reason,
    )
    db.add(log)


# ------------------------------------------------------------------ #
# User actions                                                         #
# ------------------------------------------------------------------ #

def suspend_user(db: Session, actor: User, target_id: int, reason: str) -> User:
    if actor.id == target_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot suspend your own account",
        )

    target = db.query(User).filter(User.id == target_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not target.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is already suspended"
        )

    now = datetime.now(timezone.utc)
    before = f"is_active=True"
    target.is_active = False
    target.suspended_by = actor.id
    target.suspended_at = now
    target.suspension_reason = reason

    _write_audit_log(
        db, actor, "suspend_user", "user", target_id, before, "is_active=False", reason
    )
    db.commit()
    db.refresh(target)
    return target


def reactivate_user(db: Session, actor: User, target_id: int) -> User:
    target = db.query(User).filter(User.id == target_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is already active"
        )

    target.is_active = True
    target.suspended_by = None
    target.suspended_at = None
    target.suspension_reason = None

    _write_audit_log(
        db, actor, "reactivate_user", "user", target_id, "is_active=False", "is_active=True", None
    )
    db.commit()
    db.refresh(target)
    return target


def change_user_role(db: Session, actor: User, target_id: int, new_role: str) -> User:
    if new_role not in ("client", "ba"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The super_admin role cannot be changed via this endpoint",
        )

    target = db.query(User).filter(User.id == target_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.role == UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The super_admin role cannot be changed via this endpoint",
        )

    old_role = target.role.value if target.role else None
    target.role = UserRole(new_role)

    _write_audit_log(
        db, actor, "change_role", "user", target_id, f"role={old_role}", f"role={new_role}", None
    )
    db.commit()
    db.refresh(target)
    return target


# ------------------------------------------------------------------ #
# Team actions                                                         #
# ------------------------------------------------------------------ #

def suspend_team(db: Session, actor: User, target_id: int, reason: str) -> Team:
    team = db.query(Team).filter(Team.id == target_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if team.status == TeamStatus.suspended:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Team is already suspended"
        )

    now = datetime.now(timezone.utc)
    before = f"status={team.status.value if team.status else 'active'}"
    team.status = TeamStatus.suspended
    team.suspended_by = actor.id
    team.suspended_at = now
    team.suspension_reason = reason

    _write_audit_log(
        db, actor, "suspend_team", "team", target_id, before, "status=suspended", reason
    )
    db.commit()
    db.refresh(team)
    return team


def reactivate_team(db: Session, actor: User, target_id: int) -> Team:
    team = db.query(Team).filter(Team.id == target_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if team.status != TeamStatus.suspended:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Team is not suspended"
        )

    team.status = TeamStatus.active
    team.suspended_by = None
    team.suspended_at = None
    team.suspension_reason = None

    _write_audit_log(
        db, actor, "reactivate_team", "team", target_id, "status=suspended", "status=active", None
    )
    db.commit()
    db.refresh(team)
    return team
