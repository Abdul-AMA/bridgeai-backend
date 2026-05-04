from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel


class DocumentStatusEnum(str, Enum):
    processing = "processing"
    ready = "ready"
    failed = "failed"


class DocumentOut(BaseModel):
    id: int
    project_id: int
    filename: str
    file_type: str
    status: DocumentStatusEnum
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListOut(BaseModel):
    items: List[DocumentOut]
    total: int
