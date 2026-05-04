from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class TriggerTypeEnum(str, Enum):
    document = "document"
    chat = "chat"
    manual = "manual"


class ProjectContextSummaryOut(BaseModel):
    project_id: int
    content: Optional[str]
    generated_at: Optional[datetime]
    is_generating: bool
    last_trigger: TriggerTypeEnum

    class Config:
        from_attributes = True
