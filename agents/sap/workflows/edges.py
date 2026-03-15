"""
agents/sap/workflows/edges.py
==================================
Conditional edge routing logic for the SAPAgent LangGraph workflow.

All routing functions take the graph state and return the name of the
next node to execute.

Example
-------
    def should_retry(state: dict) -> str:
        return "retry_node" if state.get("retry_count", 0) < 3 else END
"""
from __future__ import annotations


def default_router(state: dict) -> str:
    """
    Default pass-through router.
    Override this with agent-specific conditional logic.
    """
    from langgraph.graph import END
    return END
