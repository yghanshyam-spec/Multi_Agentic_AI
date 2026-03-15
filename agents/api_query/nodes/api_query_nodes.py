"""agents/api_query/nodes/api_query_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/api_query/workflows/nodes/ (one file per node).
New code should import directly from agents.api_query.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def load_api_spec_node(state):
    """Backward-compat shim — delegates to workflows/nodes/load_api_spec_node.py."""
    from agents.api_query.workflows.nodes.load_api_spec_node import load_api_spec_node as _fn
    return _fn(state)

def select_endpoint_node(state):
    """Backward-compat shim — delegates to workflows/nodes/select_endpoint_node.py."""
    from agents.api_query.workflows.nodes.select_endpoint_node import select_endpoint_node as _fn
    return _fn(state)

def build_parameters_node(state):
    """Backward-compat shim — delegates to workflows/nodes/build_parameters_node.py."""
    from agents.api_query.workflows.nodes.build_parameters_node import build_parameters_node as _fn
    return _fn(state)

def manage_auth_node(state):
    """Backward-compat shim — delegates to workflows/nodes/manage_auth_node.py."""
    from agents.api_query.workflows.nodes.manage_auth_node import manage_auth_node as _fn
    return _fn(state)

def execute_request_node(state):
    """Backward-compat shim — delegates to workflows/nodes/execute_request_node.py."""
    from agents.api_query.workflows.nodes.execute_request_node import execute_request_node as _fn
    return _fn(state)

def parse_response_node(state):
    """Backward-compat shim — delegates to workflows/nodes/parse_response_node.py."""
    from agents.api_query.workflows.nodes.parse_response_node import parse_response_node as _fn
    return _fn(state)

def handle_api_error_node(state):
    """Backward-compat shim — delegates to workflows/nodes/handle_api_error_node.py."""
    from agents.api_query.workflows.nodes.handle_api_error_node import handle_api_error_node as _fn
    return _fn(state)


__all__ = ["load_api_spec_node", "select_endpoint_node", "build_parameters_node", "manage_auth_node", "execute_request_node", "parse_response_node", "handle_api_error_node"]
