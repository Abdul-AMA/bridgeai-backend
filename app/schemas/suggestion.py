"""Schemas for creative suggestions requests and responses."""

from typing import List, Optional

from pydantic import BaseModel, Field


class SuggestionsRequest(BaseModel):
    """Schema for requesting creative suggestions."""
    
    project_id: int = Field(..., description="Project ID")
    context: Optional[str] = Field(None, description="Additional context from user")
    categories: Optional[List[str]] = Field(None, description="Specific categories to focus on")


class SuggestionResponse(BaseModel):
    """Schema for a single suggestion."""
    
    category: str = Field(..., description="Suggestion category")
    title: str = Field(..., description="Suggestion title")
    description: str = Field(..., description="Detailed description")
    value_proposition: str = Field(..., description="Value proposition")
    complexity: str = Field(..., description="Implementation complexity")
    priority: str = Field(..., description="Priority level")
