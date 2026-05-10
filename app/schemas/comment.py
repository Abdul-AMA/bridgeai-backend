"""Schemas for comment-related requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class CommentCreate(BaseModel):
    """Schema for creating a comment on a CRS document or an RTM requirement."""

    crs_id: Optional[int] = Field(None, description="ID of the CRS document (for CRS comments)")
    requirement_id: Optional[int] = Field(None, description="ID of the requirement (for RTM comments)")
    content: str = Field(..., min_length=1, description="Comment content")

    @model_validator(mode="after")
    def at_least_one_target(self):
        if self.crs_id is None and self.requirement_id is None:
            raise ValueError("Either crs_id or requirement_id must be provided")
        return self


class CommentOut(BaseModel):
    """Schema for comment response."""

    id: int
    crs_id: Optional[int]
    requirement_id: Optional[int] = None
    author_id: int
    author_name: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
