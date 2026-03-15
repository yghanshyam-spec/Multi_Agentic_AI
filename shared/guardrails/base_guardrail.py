"""
shared/guardrails/base_guardrail.py
=====================================
Abstract base class for all guardrail implementations.

Each agent's guardrails/ folder can extend BaseGuardrail:

    class AgentPolicyGuardrail(BaseGuardrail):
        def check(self, text: str, context: dict) -> GuardrailResult:
            ...

Usage inside a node:
    from shared.guardrails import BaseGuardrail, GuardrailResult
    result = MyGuardrail().check(state["raw_input"], state)
    if not result.passed:
        return {"status": "FAILED", "error_history": [result.reason]}
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GuardrailResult:
    """Result of a single guardrail check."""
    passed:     bool
    reason:     str = ""
    violations: List[str] = field(default_factory=list)
    metadata:   dict = field(default_factory=dict)


class BaseGuardrail:
    """
    Abstract base guardrail.  Subclass and implement ``check()``.

    All guardrail implementations MUST return a GuardrailResult.
    """

    name: str = "base_guardrail"

    def check(self, text: str, context: dict | None = None) -> GuardrailResult:
        raise NotImplementedError(f"{self.__class__.__name__}.check() must be implemented")

    def __call__(self, text: str, context: dict | None = None) -> GuardrailResult:
        return self.check(text, context or {})
