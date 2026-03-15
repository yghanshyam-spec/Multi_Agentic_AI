"""agents/salesforce/nodes/salesforce_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/salesforce/workflows/nodes/ (one file per node).
New code should import directly from agents.salesforce.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def parse_sf_intent_node(state):
    """Backward-compat shim — delegates to workflows/nodes/parse_sf_intent_node.py."""
    from agents.salesforce.workflows.nodes.parse_sf_intent_node import parse_sf_intent_node as _fn
    return _fn(state)

def generate_soql_node(state):
    """Backward-compat shim — delegates to workflows/nodes/generate_soql_node.py."""
    from agents.salesforce.workflows.nodes.generate_soql_node import generate_soql_node as _fn
    return _fn(state)

def call_salesforce_api_node(state):
    """Backward-compat shim — delegates to workflows/nodes/call_salesforce_api_node.py."""
    from agents.salesforce.workflows.nodes.call_salesforce_api_node import call_salesforce_api_node as _fn
    return _fn(state)

def validate_sf_records_node(state):
    """Backward-compat shim — delegates to workflows/nodes/validate_sf_records_node.py."""
    from agents.salesforce.workflows.nodes.validate_sf_records_node import validate_sf_records_node as _fn
    return _fn(state)

def enrich_sf_data_node(state):
    """Backward-compat shim — delegates to workflows/nodes/enrich_sf_data_node.py."""
    from agents.salesforce.workflows.nodes.enrich_sf_data_node import enrich_sf_data_node as _fn
    return _fn(state)

def format_sf_response_node(state):
    """Backward-compat shim — delegates to workflows/nodes/format_sf_response_node.py."""
    from agents.salesforce.workflows.nodes.format_sf_response_node import format_sf_response_node as _fn
    return _fn(state)

def log_sf_operation_node(state):
    """Backward-compat shim — delegates to workflows/nodes/log_sf_operation_node.py."""
    from agents.salesforce.workflows.nodes.log_sf_operation_node import log_sf_operation_node as _fn
    return _fn(state)


__all__ = ["parse_sf_intent_node", "generate_soql_node", "call_salesforce_api_node", "validate_sf_records_node", "enrich_sf_data_node", "format_sf_response_node", "log_sf_operation_node"]
