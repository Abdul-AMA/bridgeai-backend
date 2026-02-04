"""Project repository for database operations."""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_

from app.repositories.base_repository import BaseRepository
from app.models.project import Project, ProjectStatus


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project model operations."""

    def __init__(self, db: Session):
        """
        Initialize ProjectRepository.

        Args:
            db: Database session
        """
        super().__init__(Project, db)

    def get_by_name_and_team(
        self, name: str, team_id: int, exclude_id: Optional[int] = None
    ) -> Optional[Project]:
        """
        Get project by name and team.

        Args:
            name: Project name
            team_id: Team ID
            exclude_id: Optional project ID to exclude from search

        Returns:
            Project or None if not found
        """
        query = self.db.query(Project).filter(
            Project.name == name, Project.team_id == team_id
        )
        if exclude_id:
            query = query.filter(Project.id != exclude_id)
        return query.first()

    def get_user_projects(
        self,
        user_id: int,
        team_ids: Optional[List[int]] = None,
        status: Optional[ProjectStatus] = None,
    ) -> List[Project]:
        """
        Get all projects accessible to a user.

        Args:
            user_id: User ID
            team_ids: Optional list of team IDs to filter by
            status: Optional project status filter

        Returns:
            List of projects
        """
        query = self.db.query(Project)

        if team_ids is not None:
            query = query.filter(Project.team_id.in_(team_ids))

        if status:
            query = query.filter(Project.status == status)

        return query.all()

    def get_team_projects(
        self, team_id: int, status: Optional[ProjectStatus] = None
    ) -> List[Project]:
        """
        Get all projects for a team.

        Args:
            team_id: Team ID
            status: Optional project status filter

        Returns:
            List of projects
        """
        query = self.db.query(Project).filter(Project.team_id == team_id)
        if status:
            query = query.filter(Project.status == status)
        return query.all()

    def get_by_team(self, team_id: int) -> List[Project]:
        """
        Get all projects for a team (alias for get_team_projects).

        Args:
            team_id: Team ID

        Returns:
            List of projects
        """
        return self.get_team_projects(team_id)

    def get_pending_with_details(self, team_ids: List[int]) -> List[Project]:
        """
        Get pending projects with creator and team details eagerly loaded.

        Args:
            team_ids: List of team IDs to filter by

        Returns:
            List of pending projects
        """
        return (
            self.db.query(Project)
            .options(
                joinedload(Project.creator),
                joinedload(Project.team),
            )
            .filter(Project.team_id.in_(team_ids), Project.status == "pending")
            .order_by(Project.created_at.desc())
            .all()
        )

    def query(self):
        """
        Get a base query for Project model.

        Returns:
            SQLAlchemy query object
        """
        return self.db.query(Project)

    def get_team_project_status_counts(self, team_id: int) -> Dict[str, int]:
        """
        Get count of projects by status for a team.

        Args:
            team_id: Team ID

        Returns:
            Dictionary mapping status to count
        """
        result = (
            self.db.query(Project.status, func.count(Project.id))
            .filter(Project.team_id == team_id)
            .group_by(Project.status)
            .all()
        )
        return {status: count for status, count in result}

    def exists_by_name_and_team(
        self, name: str, team_id: int, exclude_id: Optional[int] = None
    ) -> bool:
        """
        Check if project exists with given name in team.

        Args:
            name: Project name
            team_id: Team ID
            exclude_id: Optional project ID to exclude from check

        Returns:
            True if project exists, False otherwise
        """
        return self.get_by_name_and_team(name, team_id, exclude_id) is not None
