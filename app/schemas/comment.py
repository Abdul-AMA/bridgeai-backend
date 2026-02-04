"""Schemas for comment-related requests and responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    """Schema for creating a new comment."""
    
    crs_id: int = Field(..., description="ID of the CRS document to comment on")
    content: str = Field(..., min_length=1, description="Comment content")


class CommentOut(BaseModel):
    """Schema for comment response."""
    
    id: int
    crs_id: int
    author_id: int
    author_name: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
