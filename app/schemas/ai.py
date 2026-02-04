"""Schemas for AI agent requests and responses."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RequirementInput(BaseModel):
    """Schema for requirement analysis input."""
    
    user_input: str = Field(..., description="User requirement text")
    conversation_history: Optional[List[str]] = Field(default_factory=list, description="Previous conversation")
    extracted_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Previously extracted fields")


class ClarificationResponse(BaseModel):
    """Schema for requirement clarification response."""
    
    output: str = Field(..., description="Analysis output")
    clarification_questions: List[str] = Field(default_factory=list, description="Questions for user")
    ambiguities: List[Dict[str, Any]] = Field(default_factory=list, description="Detected ambiguities")
    needs_clarification: bool = Field(..., description="Whether clarification is needed")
    clarity_score: Optional[int] = Field(None, description="Clarity score (0-100)")
    quality_summary: Optional[str] = Field(None, description="Quality summary")
    last_node: Optional[str] = Field(None, description="Last graph node executed")
