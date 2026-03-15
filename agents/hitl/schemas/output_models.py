"""
schemas/output_models.py
========================
Pydantic models for structured final responses.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    """Top-level response returned to callers."""
    answer: str = Field(..., description="The agent's final answer.")
    sources: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: str
    node: Optional[str] = None
    recoverable: bool = True
