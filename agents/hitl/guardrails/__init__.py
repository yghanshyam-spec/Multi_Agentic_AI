"""
guardrails/
===========
Safety & ethics policies applied before/after agent responses.
Add input validators, output filters, PII redactors, etc. here.
"""

from __future__ import annotations


def validate_input(text: str) -> tuple[bool, str]:
    """
    Return (is_safe, reason).
    Extend with real checks: profanity filters, PII detection, etc.
    """
    if not text or not text.strip():
        return False, "Input is empty."
    if len(text) > 10_000:
        return False, "Input exceeds maximum allowed length."
    return True, ""


def sanitize_output(text: str, max_length: int = 8192) -> str:
    """Trim and clean agent output before returning to the user."""
    return text.strip()[:max_length]
