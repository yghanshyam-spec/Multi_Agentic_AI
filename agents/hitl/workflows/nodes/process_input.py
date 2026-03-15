"""
workflows/nodes/process_input.py
=================================
Pre-processing node: validate & enrich the raw user input.
"""

from __future__ import annotations

from schemas.graph_state import AgentState
from shared.common import get_logger

logger = get_logger(__name__)


def process_input_node(state: AgentState) -> AgentState:
    """Sanitise input and attach any metadata needed downstream."""
    raw = state.get("input", "").strip()
    logger.info("Processing input", length=len(raw))

    if not raw:
        return {**state, "error": "Empty input received."}

    return {
        **state,
        "input": raw,
        "metadata": {**state.get("metadata", {}), "input_length": len(raw)},
    }
