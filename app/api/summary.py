"""
Project Context Summary API.
Endpoints: GET/POST /api/projects/{project_id}/context-summary[/regenerate]
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.summary import ProjectContextSummaryOut, TriggerTypeEnum
from app.services import summary_service
from app.services.background_summary_generator import queue_summary_generation
from app.services.permission_service import PermissionService

router = APIRouter()


@router.get(
    "/{project_id}/context-summary",
    response_model=ProjectContextSummaryOut,
)
def get_context_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the current project context summary, or a null-content record if none exists."""
    PermissionService.verify_project_access(db, project_id, current_user.id)
    row = summary_service.get_or_none(project_id, db)
    if row is None:
        return ProjectContextSummaryOut(
            project_id=project_id,
            content=None,
            generated_at=None,
            is_generating=False,
            last_trigger=TriggerTypeEnum.manual,
        )
    return row


@router.post(
    "/{project_id}/context-summary/regenerate",
    response_model=ProjectContextSummaryOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def regenerate_context_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Queue a manual summary regeneration. Idempotent — will not duplicate if already running."""
    PermissionService.verify_project_access(db, project_id, current_user.id)
    queue_summary_generation(project_id, trigger="manual")

    row = summary_service.get_or_none(project_id, db)
    if row is None:
        return ProjectContextSummaryOut(
            project_id=project_id,
            content=None,
            generated_at=None,
            is_generating=True,
            last_trigger=TriggerTypeEnum.manual,
        )
    return ProjectContextSummaryOut(
        project_id=project_id,
        content=row.content,
        generated_at=row.generated_at,
        is_generating=True,
        last_trigger=TriggerTypeEnum.manual,
    )
