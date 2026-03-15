"""agents/email_handler/nodes/email_handler_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/email_handler/workflows/nodes/ (one file per node).
New code should import directly from agents.email_handler.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def fetch_email_node(state):
    """Backward-compat shim — delegates to workflows/nodes/fetch_email_node.py."""
    from agents.email_handler.workflows.nodes.fetch_email_node import fetch_email_node as _fn
    return _fn(state)

def process_attachments_node(state):
    """Backward-compat shim — delegates to workflows/nodes/process_attachments_node.py."""
    from agents.email_handler.workflows.nodes.process_attachments_node import process_attachments_node as _fn
    return _fn(state)

def parse_email_node(state):
    """Backward-compat shim — delegates to workflows/nodes/parse_email_node.py."""
    from agents.email_handler.workflows.nodes.parse_email_node import parse_email_node as _fn
    return _fn(state)

def classify_email_node(state):
    """Backward-compat shim — delegates to workflows/nodes/classify_email_node.py."""
    from agents.email_handler.workflows.nodes.classify_email_node import classify_email_node as _fn
    return _fn(state)

def route_action_node(state):
    """Backward-compat shim — delegates to workflows/nodes/route_action_node.py."""
    from agents.email_handler.workflows.nodes.route_action_node import route_action_node as _fn
    return _fn(state)

def draft_reply_node(state):
    """Backward-compat shim — delegates to workflows/nodes/draft_reply_node.py."""
    from agents.email_handler.workflows.nodes.draft_reply_node import draft_reply_node as _fn
    return _fn(state)

def dispatch_email_node(state):
    """Backward-compat shim — delegates to workflows/nodes/dispatch_email_node.py."""
    from agents.email_handler.workflows.nodes.dispatch_email_node import dispatch_email_node as _fn
    return _fn(state)


__all__ = ["fetch_email_node", "process_attachments_node", "parse_email_node", "classify_email_node", "route_action_node", "draft_reply_node", "dispatch_email_node"]
