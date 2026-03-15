"""agents/scheduling/nodes/scheduling_agent_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/scheduling/workflows/nodes/ (one file per node).
New code should import directly from agents.scheduling.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def parse_schedule_intent_node(state):
    """Backward-compat shim — delegates to workflows/nodes/parse_schedule_intent_node.py."""
    from agents.scheduling.workflows.nodes.parse_schedule_intent_node import parse_schedule_intent_node as _fn
    return _fn(state)

def check_availability_node(state):
    """Backward-compat shim — delegates to workflows/nodes/check_availability_node.py."""
    from agents.scheduling.workflows.nodes.check_availability_node import check_availability_node as _fn
    return _fn(state)

def create_event_invitation_node(state):
    """Backward-compat shim — delegates to workflows/nodes/create_event_invitation_node.py."""
    from agents.scheduling.workflows.nodes.create_event_invitation_node import create_event_invitation_node as _fn
    return _fn(state)

def dispatch_calendar_event_node(state):
    """Backward-compat shim — delegates to workflows/nodes/dispatch_calendar_event_node.py."""
    from agents.scheduling.workflows.nodes.dispatch_calendar_event_node import dispatch_calendar_event_node as _fn
    return _fn(state)

def confirm_scheduling_node(state):
    """Backward-compat shim — delegates to workflows/nodes/confirm_scheduling_node.py."""
    from agents.scheduling.workflows.nodes.confirm_scheduling_node import confirm_scheduling_node as _fn
    return _fn(state)


__all__ = ["parse_schedule_intent_node", "check_availability_node", "create_event_invitation_node", "dispatch_calendar_event_node", "confirm_scheduling_node"]
