"""agents/workflow/nodes/workflow_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/workflow/workflows/nodes/ (one file per node).
New code should import directly from agents.workflow.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def load_workflow_definition_node(state):
    """Backward-compat shim — delegates to workflows/nodes/load_workflow_definition_node.py."""
    from agents.workflow.workflows.nodes.load_workflow_definition_node import load_workflow_definition_node as _fn
    return _fn(state)

def sequence_steps_node(state):
    """Backward-compat shim — delegates to workflows/nodes/sequence_steps_node.py."""
    from agents.workflow.workflows.nodes.sequence_steps_node import sequence_steps_node as _fn
    return _fn(state)

def dispatch_step_node(state):
    """Backward-compat shim — delegates to workflows/nodes/dispatch_step_node.py."""
    from agents.workflow.workflows.nodes.dispatch_step_node import dispatch_step_node as _fn
    return _fn(state)

def aggregate_step_results_node(state):
    """Backward-compat shim — delegates to workflows/nodes/aggregate_step_results_node.py."""
    from agents.workflow.workflows.nodes.aggregate_step_results_node import aggregate_step_results_node as _fn
    return _fn(state)

def evaluate_conditions_node(state):
    """Backward-compat shim — delegates to workflows/nodes/evaluate_conditions_node.py."""
    from agents.workflow.workflows.nodes.evaluate_conditions_node import evaluate_conditions_node as _fn
    return _fn(state)

def manage_workflow_error_node(state):
    """Backward-compat shim — delegates to workflows/nodes/manage_workflow_error_node.py."""
    from agents.workflow.workflows.nodes.manage_workflow_error_node import manage_workflow_error_node as _fn
    return _fn(state)

def summarise_workflow_node(state):
    """Backward-compat shim — delegates to workflows/nodes/summarise_workflow_node.py."""
    from agents.workflow.workflows.nodes.summarise_workflow_node import summarise_workflow_node as _fn
    return _fn(state)


__all__ = ["load_workflow_definition_node", "sequence_steps_node", "dispatch_step_node", "aggregate_step_results_node", "evaluate_conditions_node", "manage_workflow_error_node", "summarise_workflow_node"]
