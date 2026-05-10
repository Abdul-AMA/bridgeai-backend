"""
CRS Comments API endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.comment_service import (
    create_comment,
    get_comments_by_crs,
    get_comment_by_id,
)
from app.services.notification_service import notify_crs_comment_added
from app.services.permission_service import PermissionService
from app.schemas.comment import CommentCreate, CommentOut
from app.repositories.crs_repository import CRSRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository

router = APIRouter()


@router.post("/", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment_endpoint(
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a comment on a CRS document or RTM requirement."""
    from app.models.comment import Comment

    if payload.requirement_id is not None:
        # RTM requirement comment
        from app.models.requirement import Requirement, RequirementStatus

        req = (
            db.query(Requirement)
            .filter(
                Requirement.id == payload.requirement_id,
                Requirement.status == RequirementStatus.active,
            )
            .first()
        )
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found"
            )
        PermissionService.verify_project_access(db, req.project_id, current_user.id)

        comment = Comment(
            requirement_id=payload.requirement_id,
            crs_id=None,
            author_id=current_user.id,
            content=payload.content,
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)

        return CommentOut(
            id=comment.id,
            crs_id=comment.crs_id,
            requirement_id=comment.requirement_id,
            author_id=comment.author_id,
            author_name=current_user.full_name,
            content=comment.content,
            created_at=comment.created_at,
        )

    # CRS document comment (original behaviour)
    crs_repo = CRSRepository(db)
    crs = crs_repo.get_by_id(payload.crs_id)
    if not crs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="CRS document not found"
        )

    project = PermissionService.verify_project_access(db, crs.project_id, current_user.id)

    try:
        comment = create_comment(
            db,
            crs_id=payload.crs_id,
            author_id=current_user.id,
            content=payload.content,
        )
        db.commit()
        db.refresh(comment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    from app.repositories.team_repository import TeamMemberRepository

    team_member_repo = TeamMemberRepository(db)
    team_members = team_member_repo.get_team_members(project.team_id)
    notify_users = [tm.user_id for tm in team_members]
    notify_crs_comment_added(
        db, crs, project, current_user, notify_users, send_email_notification=True
    )

    return CommentOut(
        id=comment.id,
        crs_id=comment.crs_id,
        requirement_id=None,
        author_id=comment.author_id,
        author_name=current_user.full_name,
        content=comment.content,
        created_at=comment.created_at,
    )


@router.get("/", response_model=List[CommentOut])
def get_comments(
    crs_id: Optional[int] = Query(None),
    requirement_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get comments for a CRS document or an RTM requirement."""
    from app.models.comment import Comment
    from app.repositories.user_repository import UserRepository

    if requirement_id is not None:
        from app.models.requirement import Requirement, RequirementStatus

        req = (
            db.query(Requirement)
            .filter(
                Requirement.id == requirement_id,
                Requirement.status == RequirementStatus.active,
            )
            .first()
        )
        if not req:
            raise HTTPException(status_code=404, detail="Requirement not found")
        PermissionService.verify_project_access(db, req.project_id, current_user.id)

        comments = (
            db.query(Comment)
            .filter(Comment.requirement_id == requirement_id)
            .order_by(Comment.created_at.asc())
            .all()
        )
        user_repo = UserRepository(db)
        return [
            CommentOut(
                id=c.id,
                crs_id=c.crs_id,
                requirement_id=c.requirement_id,
                author_id=c.author_id,
                author_name=(user_repo.get_by_id(c.author_id).full_name if user_repo.get_by_id(c.author_id) else "Unknown"),
                content=c.content,
                created_at=c.created_at,
            )
            for c in comments
        ]

    if crs_id is None:
        raise HTTPException(status_code=400, detail="crs_id or requirement_id is required")

    crs_repo = CRSRepository(db)
    crs = crs_repo.get_by_id(crs_id)
    if not crs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="CRS document not found"
        )
    PermissionService.verify_project_access(db, crs.project_id, current_user.id)

    comments = get_comments_by_crs(db, crs_id=crs_id)
    user_repo = UserRepository(db)
    return [
        CommentOut(
            id=c.id,
            crs_id=c.crs_id,
            requirement_id=None,
            author_id=c.author_id,
            author_name=(user_repo.get_by_id(c.author_id).full_name if user_repo.get_by_id(c.author_id) else "Unknown"),
            content=c.content,
            created_at=c.created_at,
        )
        for c in comments
    ]
