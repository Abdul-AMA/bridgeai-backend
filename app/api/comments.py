"""
CRS Comments API endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
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
    """Create a comment on a CRS document."""
    # Verify CRS exists and get it
    crs_repo = CRSRepository(db)
    crs = crs_repo.get_by_id(payload.crs_id)
    if not crs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="CRS document not found"
        )

    # Verify access
    project = PermissionService.verify_project_access(db, crs.project_id, current_user.id)

    # Create comment using service
    try:
        comment = create_comment(
            db, 
            crs_id=payload.crs_id, 
            author_id=current_user.id, 
            content=payload.content
        )
        db.commit()
        db.refresh(comment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Notify team members
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
        author_id=comment.author_id,
        author_name=current_user.full_name,
        content=comment.content,
        created_at=comment.created_at,
    )


@router.get("/", response_model=List[CommentOut])
def get_comments(
    crs_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all comments for a CRS document."""
    # Verify CRS exists
    crs_repo = CRSRepository(db)
    crs = crs_repo.get_by_id(crs_id)
    if not crs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="CRS document not found"
        )

    # Verify access
    PermissionService.verify_project_access(db, crs.project_id, current_user.id)

    # Get comments using service
    comments = get_comments_by_crs(db, crs_id=crs_id)

    # Get user repository for author names
    user_repo = UserRepository(db)
    
    result = []
    for comment in comments:
        author = user_repo.get_by_id(comment.author_id)
        result.append(
            CommentOut(
                id=comment.id,
                crs_id=comment.crs_id,
                author_id=comment.author_id,
                author_name=author.full_name if author else "Unknown",
                content=comment.content,
                created_at=comment.created_at,
            )
        )

    return result
