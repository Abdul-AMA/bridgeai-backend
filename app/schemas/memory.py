"""Schemas for memory-related requests and responses."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class MemoryCreateRequest(BaseModel):
    """Schema for creating a project memory."""
    
    project_id: int = Field(..., description="Project ID")
    text: str = Field(..., description="Memory text content")
    source_type: str = Field(..., description="Source type: crs, message, comment, summary")
    source_id: int = Field(..., description="Source entity ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class MemorySearchRequest(BaseModel):
    """Schema for searching project memories."""
    
    project_id: int = Field(..., description="Project ID")
    query: str = Field(..., description="Search query")
    limit: int = Field(5, ge=1, le=20, description="Maximum number of results")
    similarity_threshold: float = Field(0.3, ge=0.0, le=1.0, description="Minimum similarity score")
