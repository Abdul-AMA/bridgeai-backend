"""Admin repository — read-only query methods for the super admin dashboard."""

import math
from datetime import date, datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.admin_audit import AdminAuditLog
from app.models.audit import CRSAuditLog
from app.models.crs import CRSDocument
from app.models.system_error_log import SystemErrorLog
from app.models.team import Team, TeamMember, TeamStatus
from app.models.user import User, UserRole


class AdminRepository:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ #
    # Overview                                                             #
    # ------------------------------------------------------------------ #

    def get_overview_stats(self) -> dict:
        total_users = self.db.query(func.count(User.id)).scalar() or 0
        active_users = (
            self.db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar()
            or 0
        )
        total_teams = self.db.query(func.count(Team.id)).scalar() or 0
        active_teams = (
            self.db.query(func.count(Team.id))
            .filter(Team.status == TeamStatus.active)
            .scalar()
            or 0
        )
        suspended_teams = (
            self.db.query(func.count(Team.id))
            .filter(Team.status == TeamStatus.suspended)
            .scalar()
            or 0
        )
        total_crs = self.db.query(func.count(CRSDocument.id)).scalar() or 0

        total_ai_tokens = 0
        try:
            from app.models.ai_usage import AIUsageLog  # type: ignore

            total_ai_tokens = (
                self.db.query(func.sum(AIUsageLog.total_tokens)).scalar() or 0
            )
        except Exception:
            pass

        seven_days_ago = datetime.utcnow()
        from datetime import timedelta

        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        ai_error_count_7d = (
            self.db.query(func.count(SystemErrorLog.id))
            .filter(SystemErrorLog.created_at >= seven_days_ago)
            .scalar()
            or 0
        )

        recent_errors = (
            self.db.query(SystemErrorLog)
            .order_by(SystemErrorLog.created_at.desc())
            .limit(5)
            .all()
        )
        recent_activity = (
            self.db.query(AdminAuditLog)
            .order_by(AdminAuditLog.created_at.desc())
            .limit(5)
            .all()
        )

        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_teams": total_teams,
            "active_teams": active_teams,
            "suspended_teams": suspended_teams,
            "total_crs_generated": total_crs,
            "total_ai_tokens": total_ai_tokens,
            "ai_error_count_7d": ai_error_count_7d,
            "recent_errors": recent_errors,
            "recent_activity": recent_activity,
        }

    # ------------------------------------------------------------------ #
    # Users                                                                #
    # ------------------------------------------------------------------ #

    def get_users_paginated(
        self,
        page: int = 1,
        page_size: int = 25,
        role: Optional[str] = None,
        status: Optional[str] = None,
        team_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        q = self.db.query(User)

        if role:
            try:
                q = q.filter(User.role == UserRole(role))
            except ValueError:
                pass
        if status == "active":
            q = q.filter(User.is_active.is_(True))
        elif status == "suspended":
            q = q.filter(User.is_active.is_(False))
        if team_id:
            q = q.join(TeamMember, TeamMember.user_id == User.id).filter(
                TeamMember.team_id == team_id
            )
        if from_date:
            q = q.filter(User.created_at >= datetime.combine(from_date, datetime.min.time()))
        if to_date:
            q = q.filter(User.created_at <= datetime.combine(to_date, datetime.max.time()))
        if search:
            pattern = f"%{search}%"
            q = q.filter(
                or_(User.full_name.ilike(pattern), User.email.ilike(pattern))
            )

        total = q.count()
        users = q.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        items = []
        for user in users:
            team_count = (
                self.db.query(func.count(TeamMember.id))
                .filter(TeamMember.user_id == user.id, TeamMember.is_active.is_(True))
                .scalar()
                or 0
            )
            items.append({**user.__dict__, "team_count": team_count})

        return items, total

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        memberships = (
            self.db.query(TeamMember, Team)
            .join(Team, Team.id == TeamMember.team_id)
            .filter(TeamMember.user_id == user_id, TeamMember.is_active.is_(True))
            .all()
        )
        team_memberships = [
            {
                "team_id": tm.team_id,
                "team_name": team.name,
                "role": tm.role.value if tm.role else None,
                "joined_at": tm.joined_at,
            }
            for tm, team in memberships
        ]

        total_crs = (
            self.db.query(func.count(CRSDocument.id))
            .filter(CRSDocument.created_by == user_id)
            .scalar()
            or 0
        )

        total_ai_tokens = 0
        try:
            from app.models.ai_usage import AIUsageLog  # type: ignore

            total_ai_tokens = (
                self.db.query(func.sum(AIUsageLog.total_tokens))
                .filter(AIUsageLog.user_id == user_id)
                .scalar()
                or 0
            )
        except Exception:
            pass

        recent_activity = (
            self.db.query(AdminAuditLog)
            .filter(AdminAuditLog.target_id == user_id, AdminAuditLog.target_type == "user")
            .order_by(AdminAuditLog.created_at.desc())
            .limit(10)
            .all()
        )
        activity_items = [
            {
                "id": log.id,
                "category": "admin_action",
                "timestamp": log.created_at,
                "actor": log.actor_email,
                "event": log.action,
                "detail": log.reason,
            }
            for log in recent_activity
        ]

        return {
            **user.__dict__,
            "team_memberships": team_memberships,
            "total_crs_count": total_crs,
            "total_ai_tokens": total_ai_tokens,
            "recent_activity": activity_items,
        }

    # ------------------------------------------------------------------ #
    # Teams                                                                #
    # ------------------------------------------------------------------ #

    def get_teams_paginated(
        self,
        page: int = 1,
        page_size: int = 25,
        status: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        q = self.db.query(Team, User).join(User, User.id == Team.created_by)

        if status:
            try:
                q = q.filter(Team.status == TeamStatus(status))
            except ValueError:
                pass
        if from_date:
            q = q.filter(Team.created_at >= datetime.combine(from_date, datetime.min.time()))
        if to_date:
            q = q.filter(Team.created_at <= datetime.combine(to_date, datetime.max.time()))
        if search:
            pattern = f"%{search}%"
            q = q.filter(
                or_(Team.name.ilike(pattern), User.email.ilike(pattern))
            )

        total = q.count()
        rows = q.order_by(Team.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        items = []
        for team, creator in rows:
            member_count = (
                self.db.query(func.count(TeamMember.id))
                .filter(TeamMember.team_id == team.id, TeamMember.is_active.is_(True))
                .scalar()
                or 0
            )
            project_count = 0
            try:
                from app.models.project import Project  # type: ignore

                project_count = (
                    self.db.query(func.count(Project.id))
                    .filter(Project.team_id == team.id)
                    .scalar()
                    or 0
                )
            except Exception:
                pass
            items.append(
                {
                    **team.__dict__,
                    "status": team.status.value if team.status else "active",
                    "creator_name": creator.full_name,
                    "creator_email": creator.email,
                    "member_count": member_count,
                    "project_count": project_count,
                }
            )

        return items, total

    def get_team_by_id(self, team_id: int) -> Optional[dict]:
        row = (
            self.db.query(Team, User)
            .join(User, User.id == Team.created_by)
            .filter(Team.id == team_id)
            .first()
        )
        if not row:
            return None
        team, creator = row

        member_rows = (
            self.db.query(TeamMember, User)
            .join(User, User.id == TeamMember.user_id)
            .filter(TeamMember.team_id == team_id, TeamMember.is_active.is_(True))
            .all()
        )
        members = [
            {
                "user_id": tm.user_id,
                "full_name": u.full_name,
                "email": u.email,
                "role": tm.role.value if tm.role else None,
                "is_active": u.is_active,
            }
            for tm, u in member_rows
        ]

        active_project_count = 0
        total_crs_count = 0
        total_ai_tokens = 0
        try:
            from app.models.project import Project  # type: ignore

            active_project_count = (
                self.db.query(func.count(Project.id))
                .filter(Project.team_id == team_id, Project.status == "active")
                .scalar()
                or 0
            )
            project_ids = [
                r[0]
                for r in self.db.query(Project.id).filter(Project.team_id == team_id).all()
            ]
            if project_ids:
                total_crs_count = (
                    self.db.query(func.count(CRSDocument.id))
                    .filter(CRSDocument.project_id.in_(project_ids))
                    .scalar()
                    or 0
                )
        except Exception:
            pass

        recent_activity = (
            self.db.query(AdminAuditLog)
            .filter(AdminAuditLog.target_id == team_id, AdminAuditLog.target_type == "team")
            .order_by(AdminAuditLog.created_at.desc())
            .limit(10)
            .all()
        )
        activity_items = [
            {
                "id": log.id,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "actor_email": log.actor_email,
                "reason": log.reason,
                "created_at": log.created_at,
            }
            for log in recent_activity
        ]

        return {
            **team.__dict__,
            "status": team.status.value if team.status else "active",
            "creator_name": creator.full_name,
            "creator_email": creator.email,
            "member_count": len(members),
            "members": members,
            "active_project_count": active_project_count,
            "total_crs_count": total_crs_count,
            "total_ai_tokens": total_ai_tokens,
            "recent_activity": activity_items,
        }

    # ------------------------------------------------------------------ #
    # Analytics                                                            #
    # ------------------------------------------------------------------ #

    def get_analytics_timeseries(
        self,
        metric: str,
        from_date: date,
        to_date: date,
        group_by: Optional[str] = None,
    ) -> dict:
        from datetime import timedelta

        labels = []
        current = from_date
        while current <= to_date:
            labels.append(current.isoformat())
            current += timedelta(days=1)

        datasets = []

        if metric == "tokens":
            try:
                from app.models.ai_usage import AIUsageLog  # type: ignore

                if group_by == "team":
                    teams = self.db.query(Team).all()
                    for team in teams:
                        data = []
                        for label in labels:
                            day = date.fromisoformat(label)
                            total = (
                                self.db.query(func.sum(AIUsageLog.total_tokens))
                                .join(User, User.id == AIUsageLog.user_id)
                                .join(TeamMember, TeamMember.user_id == User.id)
                                .filter(
                                    TeamMember.team_id == team.id,
                                    func.date(AIUsageLog.created_at) == day,
                                )
                                .scalar()
                                or 0
                            )
                            data.append(total)
                        datasets.append({"label": team.name, "data": data})
                else:
                    data = []
                    for label in labels:
                        day = date.fromisoformat(label)
                        total = (
                            self.db.query(func.sum(AIUsageLog.total_tokens))
                            .filter(func.date(AIUsageLog.created_at) == day)
                            .scalar()
                            or 0
                        )
                        data.append(total)
                    datasets.append({"label": "Total tokens", "data": data})
            except Exception:
                datasets.append({"label": "Total tokens", "data": [0] * len(labels)})

        elif metric == "crs_generations":
            data = []
            for label in labels:
                day = date.fromisoformat(label)
                total = (
                    self.db.query(func.count(CRSDocument.id))
                    .filter(func.date(CRSDocument.created_at) == day)
                    .scalar()
                    or 0
                )
                data.append(total)
            datasets.append({"label": "CRS generations", "data": data})

        elif metric == "active_users":
            data = []
            for label in labels:
                day = date.fromisoformat(label)
                total = (
                    self.db.query(func.count(func.distinct(User.id)))
                    .filter(func.date(User.created_at) <= day, User.is_active.is_(True))
                    .scalar()
                    or 0
                )
                data.append(total)
            datasets.append({"label": "Active users", "data": data})

        elif metric == "new_teams":
            data = []
            for label in labels:
                day = date.fromisoformat(label)
                total = (
                    self.db.query(func.count(Team.id))
                    .filter(func.date(Team.created_at) == day)
                    .scalar()
                    or 0
                )
                data.append(total)
            datasets.append({"label": "New teams", "data": data})

        elif metric == "ai_errors":
            data = []
            for label in labels:
                day = date.fromisoformat(label)
                total = (
                    self.db.query(func.count(SystemErrorLog.id))
                    .filter(func.date(SystemErrorLog.created_at) == day)
                    .scalar()
                    or 0
                )
                data.append(total)
            datasets.append({"label": "AI errors", "data": data})

        return {
            "metric": metric,
            "from_date": from_date,
            "to_date": to_date,
            "group_by": group_by,
            "labels": labels,
            "datasets": datasets,
        }

    # ------------------------------------------------------------------ #
    # Logs                                                                 #
    # ------------------------------------------------------------------ #

    def get_logs_paginated(
        self,
        category: str,
        page: int = 1,
        page_size: int = 25,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        actor: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        """Build a unified log list from the appropriate source table."""
        items: List[dict] = []
        total = 0

        if category in ("audit_trail",):
            q = self.db.query(AdminAuditLog)
            if from_date:
                q = q.filter(AdminAuditLog.created_at >= from_date)
            if to_date:
                q = q.filter(AdminAuditLog.created_at <= to_date)
            if actor:
                q = q.filter(AdminAuditLog.actor_email.ilike(f"%{actor}%"))
            if keyword:
                q = q.filter(AdminAuditLog.action.ilike(f"%{keyword}%"))
            total = q.count()
            rows = (
                q.order_by(AdminAuditLog.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )
            items = [
                {
                    "id": r.id,
                    "category": category,
                    "timestamp": r.created_at,
                    "actor": r.actor_email,
                    "event": r.action,
                    "detail": f"target={r.target_type}:{r.target_id} reason={r.reason}",
                }
                for r in rows
            ]

        elif category == "system":
            q = self.db.query(SystemErrorLog)
            if from_date:
                q = q.filter(SystemErrorLog.created_at >= from_date)
            if to_date:
                q = q.filter(SystemErrorLog.created_at <= to_date)
            if keyword:
                q = q.filter(SystemErrorLog.message.ilike(f"%{keyword}%"))
            total = q.count()
            rows = (
                q.order_by(SystemErrorLog.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )
            items = [
                {
                    "id": r.id,
                    "category": category,
                    "timestamp": r.created_at,
                    "actor": None,
                    "event": f"{r.method} {r.path} → {r.error_code}",
                    "detail": r.message,
                }
                for r in rows
            ]

        elif category in ("ai_generation", "user_activity", "auth", "api_errors", "token_usage"):
            # For these categories we read from the AI usage / auth log tables
            # if they exist, returning empty if they don't.
            try:
                from app.models.ai_usage import AIUsageLog  # type: ignore

                q = self.db.query(AIUsageLog)
                if from_date:
                    q = q.filter(AIUsageLog.created_at >= from_date)
                if to_date:
                    q = q.filter(AIUsageLog.created_at <= to_date)
                total = q.count()
                rows = (
                    q.order_by(AIUsageLog.created_at.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                    .all()
                )
                items = [
                    {
                        "id": r.id,
                        "category": category,
                        "timestamp": r.created_at,
                        "actor": None,
                        "event": "AI request",
                        "detail": f"tokens={getattr(r, 'total_tokens', None)}",
                    }
                    for r in rows
                ]
            except Exception:
                pass

        return items, total

    def get_audit_logs_paginated(
        self,
        page: int = 1,
        page_size: int = 25,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        actor: Optional[str] = None,
    ) -> Tuple[List[CRSAuditLog], int]:
        q = self.db.query(CRSAuditLog, User).join(User, User.id == CRSAuditLog.changed_by)
        if from_date:
            q = q.filter(CRSAuditLog.changed_at >= from_date)
        if to_date:
            q = q.filter(CRSAuditLog.changed_at <= to_date)
        if actor:
            q = q.filter(User.email.ilike(f"%{actor}%"))
        total = q.count()
        rows = (
            q.order_by(CRSAuditLog.changed_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        items = [
            {
                "id": log.id,
                "crs_id": log.crs_id,
                "action": log.action,
                "changed_by_email": user.email,
                "old_status": log.old_status,
                "new_status": log.new_status,
                "summary": log.summary,
                "changed_at": log.changed_at,
            }
            for log, user in rows
        ]
        return items, total

    def get_error_logs_paginated(
        self,
        page: int = 1,
        page_size: int = 25,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        keyword: Optional[str] = None,
    ) -> Tuple[List[SystemErrorLog], int]:
        q = self.db.query(SystemErrorLog)
        if from_date:
            q = q.filter(SystemErrorLog.created_at >= from_date)
        if to_date:
            q = q.filter(SystemErrorLog.created_at <= to_date)
        if keyword:
            q = q.filter(SystemErrorLog.message.ilike(f"%{keyword}%"))
        total = q.count()
        rows = (
            q.order_by(SystemErrorLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return rows, total
