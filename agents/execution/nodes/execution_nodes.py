"""agents/execution/nodes/execution_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/execution/workflows/nodes/ (one file per node).
New code should import directly from agents.execution.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def receive_plan_node(state):
    """Backward-compat shim — delegates to workflows/nodes/receive_plan_node.py."""
    from agents.execution.workflows.nodes.receive_plan_node import receive_plan_node as _fn
    return _fn(state)

def validate_preconditions_node(state):
    """Backward-compat shim — delegates to workflows/nodes/validate_preconditions_node.py."""
    from agents.execution.workflows.nodes.validate_preconditions_node import validate_preconditions_node as _fn
    return _fn(state)

def manage_sandbox_node(state):
    """Backward-compat shim — delegates to workflows/nodes/manage_sandbox_node.py."""
    from agents.execution.workflows.nodes.manage_sandbox_node import manage_sandbox_node as _fn
    return _fn(state)

def execute_script_node(state):
    """Backward-compat shim — delegates to workflows/nodes/execute_script_node.py."""
    from agents.execution.workflows.nodes.execute_script_node import execute_script_node as _fn
    return _fn(state)

def verify_output_node(state):
    """Backward-compat shim — delegates to workflows/nodes/verify_output_node.py."""
    from agents.execution.workflows.nodes.verify_output_node import verify_output_node as _fn
    return _fn(state)

def execute_rollback_node(state):
    """Backward-compat shim — delegates to workflows/nodes/execute_rollback_node.py."""
    from agents.execution.workflows.nodes.execute_rollback_node import execute_rollback_node as _fn
    return _fn(state)

def report_execution_node(state):
    """Backward-compat shim — delegates to workflows/nodes/report_execution_node.py."""
    from agents.execution.workflows.nodes.report_execution_node import report_execution_node as _fn
    return _fn(state)


__all__ = ["receive_plan_node", "validate_preconditions_node", "manage_sandbox_node", "execute_script_node", "verify_output_node", "execute_rollback_node", "report_execution_node"]
