"""
agents/vector_query/schemas/output_models.py
========================================
Final response schemas for the VectorQuery agent.

Uses dataclasses for zero-dependency schema definitions.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class VectorQueryOutput:
    """Standard output model for the VectorQuery agent."""
    status:     str = "COMPLETED"
    result:     Dict[str, Any] = field(default_factory=dict)
    error:      Optional[str] = None
    session_id: Optional[str] = None
    confidence: float = 0.9

    def dict(self) -> Dict[str, Any]:
        return {
            "status":     self.status,
            "result":     self.result,
            "error":      self.error,
            "session_id": self.session_id,
            "confidence": self.confidence,
        }
