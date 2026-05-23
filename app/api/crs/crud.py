"""
CRS CRUD Operations Module.
Handles basic Create, Read operations for CRS documents.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.json_utils import safe_json_loads
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.crs import CRSDocument
from app.models.user import User
from app.services.permission_service import PermissionService
from app.services.crs_service import (
    get_crs_by_id,
    get_latest_crs,
    persist_crs_document,
)
from app.services.notification_service import notify_crs_created
from app.schemas.crs import CRSCreate, CRSOut


router = APIRouter()


def _build_crs_out(crs: CRSDocument) -> CRSOut:
    """Construct a CRSOut response from a CRSDocument ORM object."""
    return CRSOut(
        id=crs.id,
        project_id=crs.project_id,
        status=crs.status.value,
        pattern=crs.pattern.value if crs.pattern else "babok",
        version=crs.version,
        edit_version=crs.edit_version if crs.edit_version is not None else 1,
        content=crs.content,
        summary_points=safe_json_loads(crs.summary_points, default=[]),
        field_sources=safe_json_loads(crs.field_sources, default=None),
        created_by=crs.created_by,
        approved_by=crs.approved_by,
        rejection_reason=crs.rejection_reason,
        reviewed_at=crs.reviewed_at,
        created_at=crs.created_at,
    )


@router.post("/", response_model=CRSOut, status_code=status.HTTP_201_CREATED)
def create_crs(
    crs_in: CRSCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new CRS document.

    A CRS can be created in either:
    - Complete state: all required fields filled (status=draft)
    - Partial state: minimum 40% complete (status=draft, allow_partial=True)

    If session_id is provided, the CRS will be linked to that session.
    """
    from app.models.session_model import SessionModel

    project = PermissionService.verify_project_access(db, crs_in.project_id, current_user.id)

    if crs_in.allow_partial:
        completeness = crs_in.completeness_percentage or 0
        if completeness < 40:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Partial CRS must be at least 40% complete. Current: {completeness}%",
            )

    crs = persist_crs_document(
        db=db,
        project_id=crs_in.project_id,
        content=crs_in.content,
        summary_points=crs_in.summary_points,
        pattern=crs_in.pattern.value if crs_in.pattern else "babok",
        created_by=current_user.id,
    )

    if crs_in.session_id:
        session = (
            db.query(SessionModel)
            .filter(SessionModel.id == crs_in.session_id)
            .first()
        )
        if session:
            session.crs_document_id = crs.id
            db.commit()

    # Notify team members after the response is sent so email latency doesn't block the caller.
    from app.models.team import TeamMember

    notify_user_ids = (
        db.query(TeamMember.user_id)
        .filter(
            TeamMember.team_id == project.team_id,
            TeamMember.is_active == True,
            TeamMember.user_id != current_user.id,
        )
        .all()
    )
    notify_users = [uid[0] for uid in notify_user_ids]
    
    notify_crs_created(db, crs, project, notify_users, send_email_notification=True)

    # Queue RTM refresh for the new CRS
    from app.services.background_rtm_generator import queue_rtm_generation_from_thread
    queue_rtm_generation_from_thread(crs_in.project_id, "save")

    # Parse summary_points and field_sources for response
    try:
        summary_points_list = json.loads(crs.summary_points) if crs.summary_points else []
    except Exception:
        summary_points_list = []

    try:
        field_sources_data = (
            json.loads(crs.field_sources) if crs.field_sources else None
        )
    except Exception:
        field_sources_data = None

    return _build_crs_out(crs)


@router.get("/latest", response_model=Optional[CRSOut])
def read_latest_crs(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch the most recent CRS for a project.
    """
    PermissionService.verify_project_access(db, project_id, current_user.id)

    crs = get_latest_crs(db, project_id=project_id)
    if not crs:
        return None

    return _build_crs_out(crs)


@router.get("/session/{session_id}", response_model=Optional[CRSOut])
def read_crs_for_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch the CRS document linked to a specific chat session.
    """
    from app.models.session_model import SessionModel

    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    PermissionService.verify_project_access(db, session.project_id, current_user.id)

    if session.crs_document_id:
        crs = (
            db.query(CRSDocument)
            .filter(CRSDocument.id == session.crs_document_id)
            .first()
        )
        if crs:
            return _build_crs_out(crs)

    return None


@router.get("/{crs_id}", response_model=CRSOut)
def read_crs(
    crs_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch a specific CRS document version by its unique ID.
    """
    crs = get_crs_by_id(db, crs_id=crs_id)
    if not crs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="CRS document not found"
        )

    PermissionService.verify_project_access(db, crs.project_id, current_user.id)

    return _build_crs_out(crs)
