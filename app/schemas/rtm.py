from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


# ── Enums ──────────────────────────────────────────────────────────────────

class RequirementStatusEnum(str, Enum):
    active = "active"
    archived = "archived"


class SourceTypeEnum(str, Enum):
    chat_message = "chat_message"
    document = "document"


class TestCaseStatusEnum(str, Enum):
    active = "active"
    archived = "archived"


class RTMTriggerEnum(str, Enum):
    save = "save"
    status_change = "status_change"
    draft = "draft"
    manual = "manual"


# ── Traceability Links ─────────────────────────────────────────────────────

class TraceabilityLinkOut(BaseModel):
    id: int
    source_type: SourceTypeEnum
    source_id: int
    excerpt: str
    is_auto_generated: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TraceabilityLinkCreate(BaseModel):
    source_type: SourceTypeEnum
    source_id: int
    excerpt: str


# ── Test Cases ─────────────────────────────────────────────────────────────

class TestCaseOut(BaseModel):
    id: int
    requirement_id: int
    title: str
    preconditions: Optional[str]
    steps: list[str]
    expected_result: str
    is_auto_generated: bool
    status: TestCaseStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        from app.core.json_utils import safe_json_loads
        steps = safe_json_loads(obj.steps, default=[])
        if not isinstance(steps, list):
            steps = [str(steps)]
        data = {
            "id": obj.id,
            "requirement_id": obj.requirement_id,
            "title": obj.title,
            "preconditions": obj.preconditions,
            "steps": steps,
            "expected_result": obj.expected_result,
            "is_auto_generated": obj.is_auto_generated,
            "status": obj.status.value if hasattr(obj.status, "value") else obj.status,
            "created_at": obj.created_at,
        }
        return cls(**data)


class TestCaseCreate(BaseModel):
    title: str
    preconditions: Optional[str] = None
    steps: list[str]
    expected_result: str


class TestCaseUpdate(BaseModel):
    title: Optional[str] = None
    preconditions: Optional[str] = None
    steps: Optional[list[str]] = None
    expected_result: Optional[str] = None


# ── Comments (inline in detail) ────────────────────────────────────────────

class CommentInlineOut(BaseModel):
    id: int
    author_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Requirements ──────────────────────────────────────────────────────────

class RequirementOut(BaseModel):
    id: int
    req_id: str
    section: str
    description: str
    full_text: str
    status: RequirementStatusEnum
    source_count: int = 0
    test_case_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class RequirementDetailOut(RequirementOut):
    source_links: list[TraceabilityLinkOut] = []
    test_cases: list[TestCaseOut] = []
    comments: list[CommentInlineOut] = []


# ── RTM Status ────────────────────────────────────────────────────────────

class RTMStatusOut(BaseModel):
    project_id: int
    is_refreshing: bool
    last_refreshed_at: Optional[datetime]
    last_trigger: Optional[RTMTriggerEnum]
    requirement_count: int
    unverified_count: int
    untested_count: int

    class Config:
        from_attributes = True


# ── Test Case Generation ──────────────────────────────────────────────────

class GenerateTestCasesRequest(BaseModel):
    requirement_ids: list[int] = []
    generate_all_untested: bool = False


class GeneratedRequirementTestCases(BaseModel):
    requirement_id: int
    test_cases: list[TestCaseOut]


class GenerateTestCasesResponse(BaseModel):
    generated: list[GeneratedRequirementTestCases]
    skipped: list[int] = []


# ── Trigger ───────────────────────────────────────────────────────────────

class RTMTriggerRequest(BaseModel):
    trigger: RTMTriggerEnum
