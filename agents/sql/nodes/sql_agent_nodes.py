"""agents/sql/nodes/sql_agent_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/sql/workflows/nodes/ (one file per node).
New code should import directly from agents.sql.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def process_input_node(state):
    """Backward-compat shim — delegates to workflows/nodes/process_input_node.py."""
    from agents.sql.workflows.nodes.process_input_node import process_input_node as _fn
    return _fn(state)

def fetch_schema_node(state):
    """Backward-compat shim — delegates to workflows/nodes/fetch_schema_node.py."""
    from agents.sql.workflows.nodes.fetch_schema_node import fetch_schema_node as _fn
    return _fn(state)

def generate_sql_node(state):
    """Backward-compat shim — delegates to workflows/nodes/generate_sql_node.py."""
    from agents.sql.workflows.nodes.generate_sql_node import generate_sql_node as _fn
    return _fn(state)

def validate_sql_node(state):
    """Backward-compat shim — delegates to workflows/nodes/validate_sql_node.py."""
    from agents.sql.workflows.nodes.validate_sql_node import validate_sql_node as _fn
    return _fn(state)

def execute_query_node(state):
    """Backward-compat shim — delegates to workflows/nodes/execute_query_node.py."""
    from agents.sql.workflows.nodes.execute_query_node import execute_query_node as _fn
    return _fn(state)

def correct_sql_node(state):
    """Backward-compat shim — delegates to workflows/nodes/correct_sql_node.py."""
    from agents.sql.workflows.nodes.correct_sql_node import correct_sql_node as _fn
    return _fn(state)

def format_output_node(state):
    """Backward-compat shim — delegates to workflows/nodes/format_output_node.py."""
    from agents.sql.workflows.nodes.format_output_node import format_output_node as _fn
    return _fn(state)


__all__ = ["process_input_node", "fetch_schema_node", "generate_sql_node", "validate_sql_node", "execute_query_node", "correct_sql_node", "format_output_node"]
