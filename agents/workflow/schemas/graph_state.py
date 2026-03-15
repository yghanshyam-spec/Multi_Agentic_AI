"""
agents/workflow/schemas/graph_state.py
======================================
Graph state definition for the Workflow agent.

Extends BaseAgentState with agent-specific fields.
Import this TypedDict in graph.py and all node functions.
"""
from __future__ import annotations
from shared.state import BaseAgentState


class WorkflowGraphState(BaseAgentState):
    """
    Extended state for Workflow.

    Add agent-specific state fields here.
    All fields must have defaults or be Optional to avoid initialisation errors.
    """
    pass  # Add agent-specific fields below
