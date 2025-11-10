from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TeamRole(str, Enum):
    owner = "owner"
    admin = "admin" 
    member = "member"
    viewer = "viewer"


class TeamStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    archived = "archived"


# Team schemas
class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TeamStatus] = None


class TeamMemberOut(BaseModel):
    id: int
    user_id: int
    role: TeamRole
    is_active: bool
    joined_at: datetime
    
    class Config:
        from_attributes = True


class TeamOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: TeamStatus
    created_by: int
    created_at: datetime
    updated_at: datetime
    members: Optional[List[TeamMemberOut]] = []
    
    class Config:
        from_attributes = True


class TeamListOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: TeamStatus
    created_by: int
    created_at: datetime
    member_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# Team member schemas
class TeamMemberCreate(BaseModel):
    user_id: int
    role: Optional[TeamRole] = TeamRole.member


class TeamMemberUpdate(BaseModel):
    role: Optional[TeamRole] = None
    is_active: Optional[bool] = None


class TeamMemberDetailOut(BaseModel):
    id: int
    team_id: int
    user_id: int
    role: TeamRole
    is_active: bool
    joined_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True