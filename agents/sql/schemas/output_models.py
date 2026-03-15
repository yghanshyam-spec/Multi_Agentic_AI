"""
agents/sql/schemas/output_models.py
========================================
Final response schemas for the SqlAgent agent.

Uses dataclasses for zero-dependency schema definitions.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SqlAgentOutput:
    """Standard output model for the SqlAgent agent."""
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
