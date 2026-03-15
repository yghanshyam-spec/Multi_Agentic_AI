"""agents/intent/nodes/intent_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/intent/workflows/nodes/ (one file per node).
New code should import directly from agents.intent.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def normalise_input_node(state):
    """Backward-compat shim — delegates to workflows/nodes/normalise_input_node.py."""
    from agents.intent.workflows.nodes.normalise_input_node import normalise_input_node as _fn
    return _fn(state)

def classify_intent_node(state):
    """Backward-compat shim — delegates to workflows/nodes/classify_intent_node.py."""
    from agents.intent.workflows.nodes.classify_intent_node import classify_intent_node as _fn
    return _fn(state)

def extract_entities_node(state):
    """Backward-compat shim — delegates to workflows/nodes/extract_entities_node.py."""
    from agents.intent.workflows.nodes.extract_entities_node import extract_entities_node as _fn
    return _fn(state)

def route_by_confidence_node(state):
    """Backward-compat shim — delegates to workflows/nodes/route_by_confidence_node.py."""
    from agents.intent.workflows.nodes.route_by_confidence_node import route_by_confidence_node as _fn
    return _fn(state)

def request_clarification_node(state):
    """Backward-compat shim — delegates to workflows/nodes/request_clarification_node.py."""
    from agents.intent.workflows.nodes.request_clarification_node import request_clarification_node as _fn
    return _fn(state)

def split_multi_intent_node(state):
    """Backward-compat shim — delegates to workflows/nodes/split_multi_intent_node.py."""
    from agents.intent.workflows.nodes.split_multi_intent_node import split_multi_intent_node as _fn
    return _fn(state)

def aggregate_responses_node(state):
    """Backward-compat shim — delegates to workflows/nodes/aggregate_responses_node.py."""
    from agents.intent.workflows.nodes.aggregate_responses_node import aggregate_responses_node as _fn
    return _fn(state)


__all__ = ["normalise_input_node", "classify_intent_node", "extract_entities_node", "route_by_confidence_node", "request_clarification_node", "split_multi_intent_node", "aggregate_responses_node"]
