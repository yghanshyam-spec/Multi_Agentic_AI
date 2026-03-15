"""
workflows/nodes/format_output.py
=================================
Post-processing node: shape the agent's raw output for callers.
"""

from __future__ import annotations

from schemas.graph_state import AgentState
from shared.common import get_logger

logger = get_logger(__name__)


def format_output_node(state: AgentState) -> AgentState:
    output = state.get("output") or state.get("error") or "No output produced."
    logger.info("Formatting output", chars=len(output))
    return {**state, "output": output.strip()}
