"""agents/hitl/core/provider.py — LLM provider for HITL agent."""
from __future__ import annotations
from shared.common import get_llm
def get_agent_llm(**overrides):
    """Return LLM for HITL (deterministic: temperature=0.0)."""
    return get_llm(temperature=overrides.pop('temperature', 0.0), **overrides)
