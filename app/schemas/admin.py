from datetime import date, datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

from app.models.user import UserRole

T = TypeVar("T")


class PaginatedResponse(GenericModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


# ---------- Overview ----------

class AdminRecentErrorOut(BaseModel):
    id: int
    error_code: str
    path: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class AdminRecentActivityOut(BaseModel):
    id: int
    action: str
    target_type: str
    target_id: int
    actor_email: str
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminOverviewStatsOut(BaseModel):
    total_users: int
    active_users: int
    total_teams: int
    active_teams: int
    suspended_teams: int
    total_crs_generated: int
    total_ai_tokens: int
    ai_error_count_7d: int
    recent_errors: List[AdminRecentErrorOut]
    recent_activity: List[AdminRecentActivityOut]


# ---------- Users ----------

class AdminUserListItemOut(BaseModel):
    id: int
    full_name: str
    email: str
    role: Optional[str] = None
    is_active: bool
    suspended_by: Optional[int] = None
    suspension_reason: Optional[str] = None
    team_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class AdminUserTeamMembershipOut(BaseModel):
    team_id: int
    team_name: str
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class AdminUserActivityOut(BaseModel):
    id: int
    category: str
    timestamp: datetime
    actor: str
    event: str
    detail: Optional[str] = None

    class Config:
        from_attributes = True


class AdminUserDetailOut(BaseModel):
    id: int
    full_name: str
    email: str
    role: Optional[str] = None
    is_active: bool
    suspended_by: Optional[int] = None
    suspended_at: Optional[datetime] = None
    suspension_reason: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    team_memberships: List[AdminUserTeamMembershipOut]
    total_crs_count: int
    total_ai_tokens: int
    recent_activity: List[AdminUserActivityOut]

    class Config:
        from_attributes = True


class AdminUserStatusOut(BaseModel):
    id: int
    is_active: bool
    suspended_by: Optional[int] = None
    suspended_at: Optional[datetime] = None
    suspension_reason: Optional[str] = None

    class Config:
        from_attributes = True


class AdminUserRoleOut(BaseModel):
    id: int
    role: str
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- Teams ----------

class AdminTeamListItemOut(BaseModel):
    id: int
    name: str
    creator_name: str
    creator_email: str
    status: str
    suspension_reason: Optional[str] = None
    member_count: int
    project_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class AdminTeamMemberOut(BaseModel):
    user_id: int
    full_name: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class AdminTeamDetailOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    creator_name: str
    creator_email: str
    status: str
    suspended_by: Optional[int] = None
    suspended_at: Optional[datetime] = None
    suspension_reason: Optional[str] = None
    member_count: int
    members: List[AdminTeamMemberOut]
    active_project_count: int
    total_crs_count: int
    total_ai_tokens: int
    created_at: datetime
    recent_activity: List[AdminRecentActivityOut]

    class Config:
        from_attributes = True


class AdminTeamStatusOut(BaseModel):
    id: int
    status: str
    suspended_by: Optional[int] = None
    suspended_at: Optional[datetime] = None
    suspension_reason: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Actions ----------

class AdminSuspendRequest(BaseModel):
    action: str = Field(..., pattern="^(suspend|reactivate)$")
    reason: Optional[str] = Field(None, min_length=1)


class AdminChangeRoleRequest(BaseModel):
    role: str = Field(..., pattern="^(client|ba)$")


# ---------- Analytics ----------

class AdminAnalyticsDataset(BaseModel):
    label: str
    data: List[float]


class AdminTimeSeriesOut(BaseModel):
    metric: str
    from_date: date
    to_date: date
    group_by: Optional[str] = None
    labels: List[str]
    datasets: List[AdminAnalyticsDataset]


# ---------- Logs ----------

class AdminLogEntryOut(BaseModel):
    id: int
    category: str
    timestamp: datetime
    actor: Optional[str] = None
    event: str
    detail: Optional[str] = None

    class Config:
        from_attributes = True


class AdminLogPageOut(BaseModel):
    category: str
    items: List[AdminLogEntryOut]
    total: int
    page: int
    page_size: int
    pages: int


class AdminAuditLogOut(BaseModel):
    id: int
    crs_id: int
    action: str
    changed_by_email: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    summary: Optional[str] = None
    changed_at: datetime

    class Config:
        from_attributes = True


class AdminErrorLogOut(BaseModel):
    id: int
    error_code: str
    path: str
    method: str
    message: str
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
