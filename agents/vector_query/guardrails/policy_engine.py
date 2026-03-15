"""
agents/vector_query/guardrails/policy_engine.py
==========================================
Policy engine for the VectorQuery agent.

Checks inputs against policies defined in policies.yaml.
"""
from __future__ import annotations
import re
from shared.guardrails import BaseGuardrail, GuardrailResult


class VectorQueryPolicyGuardrail(BaseGuardrail):
    """Content safety and policy checker for VectorQuery."""

    name = "vector_query_policy"

    def check(self, text: str, context: dict | None = None) -> GuardrailResult:
        if not text:
            return GuardrailResult(passed=True)

        violations = []

        # Input length check
        if len(text) > 32000:
            violations.append(f"Input exceeds 32,000 chars (got {len(text)})")

        # Basic PII patterns
        if re.search(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", text):
            violations.append("Potential credit card number detected")

        return GuardrailResult(
            passed=len(violations) == 0,
            violations=violations,
            reason="; ".join(violations) if violations else "OK",
        )
