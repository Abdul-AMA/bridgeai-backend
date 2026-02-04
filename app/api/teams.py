from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.rate_limit import limiter
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.invitation import Invitation
from app.models.project import Project, ProjectStatus
from app.models.session_model import SessionModel
from app.models.crs import CRSDocument
from app.models.team import Team, TeamMember, TeamRole, TeamStatus
from app.models.user import User
from app.schemas.invitation import InvitationCreate, InvitationOut, InvitationResponse
from app.schemas.team import (
    TeamCreate,
    TeamDashboardStatsOut,
    TeamListOut,
    TeamMemberCreate,
    TeamMemberDetailOut,
    TeamMemberUpdate,
    TeamOut,
    TeamUpdate,
    ProjectStats,
    ChatStats,
    CRSStats,
    ProjectSimpleOut,
)
from app.utils.invitation import (
    build_invitation_link,
    create_invitation,
    send_invitation_email_to_console,
)
from app.services.permission_service import PermissionService
from app.services import notification_service
from app.services.team_service import TeamService

router = APIRouter()


# Team CRUD endpoints
@router.post("/", response_model=TeamOut)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new team. The creator automatically becomes the owner."""
    return TeamService.create_team(
        db=db,
        name=payload.name,
        description=payload.description,
        current_user=current_user,
    )


@router.get("/", response_model=List[TeamListOut])
def list_teams(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[TeamStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List teams. Users can see teams they are members of."""
    return TeamService.list_teams(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
    )


@router.get("/{team_id}", response_model=TeamOut)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get team details. Only team members can view team details."""
    return TeamService.get_team(db=db, team_id=team_id, current_user=current_user)


@router.put("/{team_id}", response_model=TeamOut)
def update_team(
    team_id: int,
    payload: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update team. Only owners and admins can update teams."""
    update_data = payload.dict(exclude_unset=True)
    return TeamService.update_team(
        db=db,
        team_id=team_id,
        current_user=current_user,
        name=update_data.get("name"),
        description=update_data.get("description"),
        status_update=update_data.get("status"),
    )


@router.delete("/{team_id}")
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete team. Only owners can delete teams."""
    # Check if user is owner
    PermissionService.verify_team_owner(db, team_id, current_user.id)

    team = PermissionService.get_team_or_404(db, team_id)

    # Check if team has projects
    project_count = (
        db.query(func.count(Project.id)).filter(Project.team_id == team_id).scalar()
    )
    if project_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete team with {project_count} project(s). Please delete or move all projects first, or archive the team instead.",
        )

    db.delete(team)
    db.commit()

    return {"message": "Team deleted successfully"}


# Team member management endpoints
@router.post("/{team_id}/members", response_model=TeamMemberDetailOut)
def add_team_member(
    team_id: int,
    payload: TeamMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a member to the team. Only owners and admins can add members."""
    return TeamService.add_member(
        db=db,
        team_id=team_id,
        user_id=payload.user_id,
        role=payload.role,
        current_user=current_user,
    )


@router.get("/{team_id}/members", response_model=List[TeamMemberDetailOut])
def list_team_members(
    team_id: int,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List team members. Only team members can view the member list."""
    return TeamService.list_members(
        db=db, team_id=team_id, current_user=current_user, include_inactive=include_inactive
    )


@router.put("/{team_id}/members/{member_id}", response_model=TeamMemberDetailOut)
def update_team_member(
    team_id: int,
    member_id: int,
    payload: TeamMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update team member role or status. Only owners and admins can update members."""
    update_data = payload.dict(exclude_unset=True)
    return TeamService.update_member(
        db=db,
        team_id=team_id,
        member_id=member_id,
        current_user=current_user,
        role=update_data.get("role"),
        is_active=update_data.get("is_active"),
    )


@router.delete("/{team_id}/members/{member_id}")
def remove_team_member(
    team_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a member from the team. Only owners and admins can remove members."""
    return TeamService.remove_member(
        db=db, team_id=team_id, member_id=member_id, current_user=current_user
    )


@router.get("/{team_id}/projects")
def list_team_projects(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List projects belonging to a team. Only team members can view projects."""
    return TeamService.list_team_projects(db=db, team_id=team_id, current_user=current_user)


@router.post("/{team_id}/invite", response_model=InvitationResponse)
@limiter.limit("10/hour")
def invite_team_member(
    request: Request,
    team_id: int,
    payload: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Invite a user to join the team by email. Only owners and admins can invite."""
    return TeamService.invite_member(
        db=db,
        team_id=team_id,
        email=payload.email,
        role=payload.role,
        current_user=current_user,
    )


@router.get("/{team_id}/invitations", response_model=List[InvitationOut])
def list_team_invitations(
    team_id: int,
    include_expired: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all invitations for a team.
    Only team owners and admins can view invitations.
    """
    return TeamService.list_invitations(
        db=db, team_id=team_id, current_user=current_user, include_expired=include_expired
    )


@router.delete("/{team_id}/invitations/{invitation_id}")
@limiter.limit("20/minute")
def cancel_invitation(
    request: Request,
    team_id: int,
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cancel a pending invitation.
    Only team owners and admins can cancel invitations.
    """
    return TeamService.cancel_invitation(
        db=db, team_id=team_id, invitation_id=invitation_id, current_user=current_user
    )


@router.get("/{team_id}/dashboard/stats", response_model=TeamDashboardStatsOut)
def get_team_dashboard_stats(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get aggregated statistics for team dashboard.
    
    Returns:
    - Project counts by status
    - Chat counts by status (aggregated from all team projects)
    - CRS counts by status (aggregated from all team projects)
    - Top 10 recent projects
    """
    # Verify team access - check if user is a member of the team
    PermissionService.verify_team_membership(db, team_id, current_user.id)
    
    # Get all team projects
    team_projects = db.query(Project).filter(Project.team_id == team_id).all()
    project_ids = [p.id for p in team_projects]
    
    # Calculate project statistics
    project_stats_query = (
        db.query(Project.status, func.count(Project.id))
        .filter(Project.team_id == team_id)
        .group_by(Project.status)
        .all()
    )
    
    project_by_status = {status: count for status, count in project_stats_query}
    project_total = sum(project_by_status.values())
    
    # Calculate chat statistics (aggregated from all projects)
    chat_stats = {"total": 0, "by_status": {}}
    if project_ids:
        chat_stats_query = (
            db.query(SessionModel.status, func.count(SessionModel.id))
            .filter(SessionModel.project_id.in_(project_ids))
            .group_by(SessionModel.status)
            .all()
        )
        chat_stats["by_status"] = {
            status.value if hasattr(status, 'value') else str(status): count 
            for status, count in chat_stats_query
        }
        chat_stats["total"] = sum(chat_stats["by_status"].values())
    
    # Calculate CRS statistics (aggregated from all projects)
    crs_stats = {"total": 0, "by_status": {}}
    if project_ids:
        crs_stats_query = (
            db.query(CRSDocument.status, func.count(CRSDocument.id))
            .filter(CRSDocument.project_id.in_(project_ids))
            .group_by(CRSDocument.status)
            .all()
        )
        crs_stats["by_status"] = {
            status.value if hasattr(status, 'value') else str(status): count 
            for status, count in crs_stats_query
        }
        crs_stats["total"] = sum(crs_stats["by_status"].values())
    
    # Get top 10 recent projects
    recent_projects = (
        db.query(Project)
        .filter(Project.team_id == team_id)
        .order_by(Project.created_at.desc())
        .limit(3)
        .all()
    )
    
    return TeamDashboardStatsOut(
        projects=ProjectStats(
            total=project_total,
            by_status=project_by_status
        ),
        chats=ChatStats(
            total=chat_stats["total"],
            by_status=chat_stats["by_status"]
        ),
        crs=CRSStats(
            total=crs_stats["total"],
            by_status=crs_stats["by_status"]
        ),
        recent_projects=[
            ProjectSimpleOut(
                id=p.id,
                name=p.name,
                description=p.description,
                status=p.status.value if hasattr(p.status, 'value') else str(p.status),
                created_at=p.created_at
            )
            for p in recent_projects
        ]
    )
