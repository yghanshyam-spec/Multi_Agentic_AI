"""agents/planner/nodes/planner_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/planner/workflows/nodes/ (one file per node).
New code should import directly from agents.planner.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def analyse_goal_node(state):
    """Backward-compat shim — delegates to workflows/nodes/analyse_goal_node.py."""
    from agents.planner.workflows.nodes.analyse_goal_node import analyse_goal_node as _fn
    return _fn(state)

def decompose_tasks_node(state):
    """Backward-compat shim — delegates to workflows/nodes/decompose_tasks_node.py."""
    from agents.planner.workflows.nodes.decompose_tasks_node import decompose_tasks_node as _fn
    return _fn(state)

def resolve_dependencies_node(state):
    """Backward-compat shim — delegates to workflows/nodes/resolve_dependencies_node.py."""
    from agents.planner.workflows.nodes.resolve_dependencies_node import resolve_dependencies_node as _fn
    return _fn(state)

def assign_agents_node(state):
    """Backward-compat shim — delegates to workflows/nodes/assign_agents_node.py."""
    from agents.planner.workflows.nodes.assign_agents_node import assign_agents_node as _fn
    return _fn(state)

def estimate_resources_node(state):
    """Backward-compat shim — delegates to workflows/nodes/estimate_resources_node.py."""
    from agents.planner.workflows.nodes.estimate_resources_node import estimate_resources_node as _fn
    return _fn(state)

def validate_plan_node(state):
    """Backward-compat shim — delegates to workflows/nodes/validate_plan_node.py."""
    from agents.planner.workflows.nodes.validate_plan_node import validate_plan_node as _fn
    return _fn(state)

def serialise_plan_node(state):
    """Backward-compat shim — delegates to workflows/nodes/serialise_plan_node.py."""
    from agents.planner.workflows.nodes.serialise_plan_node import serialise_plan_node as _fn
    return _fn(state)


__all__ = ["analyse_goal_node", "decompose_tasks_node", "resolve_dependencies_node", "assign_agents_node", "estimate_resources_node", "validate_plan_node", "serialise_plan_node"]
