"""agents/mcp_invoker/nodes/mcp_invoker_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/mcp_invoker/workflows/nodes/ (one file per node).
New code should import directly from agents.mcp_invoker.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def load_mcp_registry_node(state):
    """Backward-compat shim — delegates to workflows/nodes/load_mcp_registry_node.py."""
    from agents.mcp_invoker.workflows.nodes.load_mcp_registry_node import load_mcp_registry_node as _fn
    return _fn(state)

def negotiate_capabilities_node(state):
    """Backward-compat shim — delegates to workflows/nodes/negotiate_capabilities_node.py."""
    from agents.mcp_invoker.workflows.nodes.negotiate_capabilities_node import negotiate_capabilities_node as _fn
    return _fn(state)

def select_mcp_tool_node(state):
    """Backward-compat shim — delegates to workflows/nodes/select_mcp_tool_node.py."""
    from agents.mcp_invoker.workflows.nodes.select_mcp_tool_node import select_mcp_tool_node as _fn
    return _fn(state)

def marshall_mcp_request_node(state):
    """Backward-compat shim — delegates to workflows/nodes/marshall_mcp_request_node.py."""
    from agents.mcp_invoker.workflows.nodes.marshall_mcp_request_node import marshall_mcp_request_node as _fn
    return _fn(state)

def dispatch_mcp_call_node(state):
    """Backward-compat shim — delegates to workflows/nodes/dispatch_mcp_call_node.py."""
    from agents.mcp_invoker.workflows.nodes.dispatch_mcp_call_node import dispatch_mcp_call_node as _fn
    return _fn(state)

def unmarshall_mcp_response_node(state):
    """Backward-compat shim — delegates to workflows/nodes/unmarshall_mcp_response_node.py."""
    from agents.mcp_invoker.workflows.nodes.unmarshall_mcp_response_node import unmarshall_mcp_response_node as _fn
    return _fn(state)

def handle_mcp_error_node(state):
    """Backward-compat shim — delegates to workflows/nodes/handle_mcp_error_node.py."""
    from agents.mcp_invoker.workflows.nodes.handle_mcp_error_node import handle_mcp_error_node as _fn
    return _fn(state)


__all__ = ["load_mcp_registry_node", "negotiate_capabilities_node", "select_mcp_tool_node", "marshall_mcp_request_node", "dispatch_mcp_call_node", "unmarshall_mcp_response_node", "handle_mcp_error_node"]
