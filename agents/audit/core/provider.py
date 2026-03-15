"""
agents/audit/core/provider.py
================================
LLM provider wrapper for the Audit agent.

All LLM instantiation is delegated to shared/llm_factory.py.
This file exists as the standard extension point for any agent-specific
LLM configuration overrides (e.g. lower temperature for deterministic outputs).

    from agents.audit.core.provider import get_agent_llm
    llm = get_agent_llm()
"""
from __future__ import annotations
from shared.common import get_llm


def get_agent_llm(**overrides):
    """
    Return an LLM configured for the Audit agent.

    Pass keyword overrides (temperature, max_tokens) to customise
    beyond the root .env defaults without changing shared config.

    Examples
    --------
        llm = get_agent_llm(temperature=0.0)   # deterministic for structured output
        llm = get_agent_llm(max_tokens=8192)   # extended for long generation
    """
    return get_llm(**overrides)
