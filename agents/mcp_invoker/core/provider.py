"""
agents/mcp_invoker/core/provider.py
LLM provider — delegates to shared/llm_factory.py.
"""
from __future__ import annotations
from shared.common import get_llm


def get_agent_llm(**overrides):
    """Return an LLM for the mcp_invoker agent (overrides: temperature, max_tokens)."""
    return get_llm(**overrides)
