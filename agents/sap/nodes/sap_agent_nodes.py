"""agents/sap/nodes/sap_agent_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/sap/workflows/nodes/ (one file per node).
New code should import directly from agents.sap.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def parse_sap_intent_node(state):
    """Backward-compat shim — delegates to workflows/nodes/parse_sap_intent_node.py."""
    from agents.sap.workflows.nodes.parse_sap_intent_node import parse_sap_intent_node as _fn
    return _fn(state)

def select_bapi_node(state):
    """Backward-compat shim — delegates to workflows/nodes/select_bapi_node.py."""
    from agents.sap.workflows.nodes.select_bapi_node import select_bapi_node as _fn
    return _fn(state)

def call_sap_rfc_node(state):
    """Backward-compat shim — delegates to workflows/nodes/call_sap_rfc_node.py."""
    from agents.sap.workflows.nodes.call_sap_rfc_node import call_sap_rfc_node as _fn
    return _fn(state)

def parse_bapi_return_node(state):
    """Backward-compat shim — delegates to workflows/nodes/parse_bapi_return_node.py."""
    from agents.sap.workflows.nodes.parse_bapi_return_node import parse_bapi_return_node as _fn
    return _fn(state)

def handle_sap_exception_node(state):
    """Backward-compat shim — delegates to workflows/nodes/handle_sap_exception_node.py."""
    from agents.sap.workflows.nodes.handle_sap_exception_node import handle_sap_exception_node as _fn
    return _fn(state)

def transform_sap_data_node(state):
    """Backward-compat shim — delegates to workflows/nodes/transform_sap_data_node.py."""
    from agents.sap.workflows.nodes.transform_sap_data_node import transform_sap_data_node as _fn
    return _fn(state)

def summarise_sap_response_node(state):
    """Backward-compat shim — delegates to workflows/nodes/summarise_sap_response_node.py."""
    from agents.sap.workflows.nodes.summarise_sap_response_node import summarise_sap_response_node as _fn
    return _fn(state)


__all__ = ["parse_sap_intent_node", "select_bapi_node", "call_sap_rfc_node", "parse_bapi_return_node", "handle_sap_exception_node", "transform_sap_data_node", "summarise_sap_response_node"]
