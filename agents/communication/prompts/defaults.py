"""
agents/communication/prompts/defaults.py
Built-in prompt defaults for the Communication agent.
Used as fallback when Langfuse registry has no matching entry.
"""
from __future__ import annotations

_REGISTRY: dict[str, str] = {}

def get_default_prompt(key: str) -> str:
    return _REGISTRY.get(key, "")
