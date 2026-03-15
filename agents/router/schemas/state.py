"""
agents/router/schemas/state.py
================================
RouterAgentState — the canonical state TypedDict used by all router nodes
and the LangGraph StateGraph.

Imported directly from shared.state so the schema is defined in one place
and is consistent with the rest of the accelerator.
"""
from __future__ import annotations
from shared.state import RouterAgentState  # noqa: F401 — re-export

__all__ = ["RouterAgentState"]
