from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.project import (
    ProjectApprovalRequest,
    ProjectCreate,
    ProjectDashboardStatsOut,
    ProjectOut,
    ProjectRejectionRequest,
    ProjectUpdate,
    SessionSimpleOut,
    LatestCRSOut,
)
from app.models.project import ProjectStatus
from app.services.project_service import ProjectService

router = APIRouter()


# ==================== Endpoints ====================


@router.get("/pending", response_model=list[ProjectOut])
def list_pending_projects(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    List all pending project requests for BA review.
    Only Business Analysts can access this endpoint.
    Returns pending projects from all teams the BA is a member of.
    """
    return ProjectService.list_pending_projects(db, current_user)


@router.post("/", response_model=ProjectOut)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new project with role-based approval workflow:
    - BA: Creates project directly (auto-approved)
    - Client: Creates project request (pending BA approval)
    """
    project = ProjectService.create_project(
        db, payload.name, payload.description, payload.team_id, current_user
    )
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get project details. Only team members can view."""
    return ProjectService.get_project(db, project_id, current_user)


@router.get("/", response_model=list[ProjectOut])
def list_projects(
    team_id: Optional[int] = None,
    status: Optional[ProjectStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List projects.
    - BA: Can see all projects in their teams
    - Client: Can see approved projects + their own pending requests
    """
    return ProjectService.list_projects(db, current_user, team_id, status)


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update project details (name, description).
    Only the creator or BAs can update.
    """
    project = ProjectService.update_project(
        db, project_id, current_user, payload.name, payload.description, payload.status
    )
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/approve", response_model=ProjectOut)
def approve_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a pending project request. Only BAs can approve."""
    return ProjectService.approve_project(db, project_id, current_user)


@router.post("/{project_id}/reject", response_model=ProjectOut)
def reject_project(
    project_id: int,
    payload: ProjectRejectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a pending project request. Only BAs can reject."""
    return ProjectService.reject_project(
        db, project_id, current_user, payload.rejection_reason
    )


@router.get("/{project_id}/dashboard/stats", response_model=ProjectDashboardStatsOut)
def get_project_dashboard_stats(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get aggregated statistics for project dashboard.
    
    Returns:
    - Chat counts by status with total messages
    - CRS counts by status with latest CRS info
    - Document counts from memory
    - Top 5 recent chats
    """
    stats = ProjectService.get_dashboard_stats(db, project_id, current_user)
    
    # Convert to response model
    latest_crs = None
    if stats["crs"]["latest"]:
        latest_crs_data = stats["crs"]["latest"]
        latest_crs = LatestCRSOut(
            id=latest_crs_data["id"],
            version=latest_crs_data["version"],
            status=latest_crs_data["status"],
            pattern=latest_crs_data["pattern"],
            created_at=latest_crs_data["created_at"]
        )
    
    recent_chats = [
        SessionSimpleOut(
            id=chat["id"],
            name=chat["name"],
            status=chat["status"],
            started_at=chat["started_at"],
            ended_at=chat["ended_at"],
            message_count=chat["message_count"]
        )
        for chat in stats["recent_chats"]
    ]
    
    return ProjectDashboardStatsOut(
        chats={
            "total": stats["chats"]["total"],
            "by_status": stats["chats"]["by_status"],
            "total_messages": stats["chats"]["total_messages"]
        },
        crs={
            "total": stats["crs"]["total"],
            "by_status": stats["crs"]["by_status"],
            "latest": latest_crs,
            "version_count": stats["crs"]["version_count"]
        },
        documents={
            "total": stats["documents"]["total"]
        },
        recent_chats=recent_chats
    )
