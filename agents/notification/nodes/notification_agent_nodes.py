"""agents/notification/nodes/notification_agent_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/notification/workflows/nodes/ (one file per node).
New code should import directly from agents.notification.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def receive_event_node(state):
    """Backward-compat shim — delegates to workflows/nodes/receive_event_node.py."""
    from agents.notification.workflows.nodes.receive_event_node import receive_event_node as _fn
    return _fn(state)

def enrich_event_context_node(state):
    """Backward-compat shim — delegates to workflows/nodes/enrich_event_context_node.py."""
    from agents.notification.workflows.nodes.enrich_event_context_node import enrich_event_context_node as _fn
    return _fn(state)

def resolve_recipients_node(state):
    """Backward-compat shim — delegates to workflows/nodes/resolve_recipients_node.py."""
    from agents.notification.workflows.nodes.resolve_recipients_node import resolve_recipients_node as _fn
    return _fn(state)

def classify_priority_node(state):
    """Backward-compat shim — delegates to workflows/nodes/classify_priority_node.py."""
    from agents.notification.workflows.nodes.classify_priority_node import classify_priority_node as _fn
    return _fn(state)

def select_channel_node(state):
    """Backward-compat shim — delegates to workflows/nodes/select_channel_node.py."""
    from agents.notification.workflows.nodes.select_channel_node import select_channel_node as _fn
    return _fn(state)

def craft_message_node(state):
    """Backward-compat shim — delegates to workflows/nodes/craft_message_node.py."""
    from agents.notification.workflows.nodes.craft_message_node import craft_message_node as _fn
    return _fn(state)

def deduplicate_notification_node(state):
    """Backward-compat shim — delegates to workflows/nodes/deduplicate_notification_node.py."""
    from agents.notification.workflows.nodes.deduplicate_notification_node import deduplicate_notification_node as _fn
    return _fn(state)

def dispatch_notification_node(state):
    """Backward-compat shim — delegates to workflows/nodes/dispatch_notification_node.py."""
    from agents.notification.workflows.nodes.dispatch_notification_node import dispatch_notification_node as _fn
    return _fn(state)

def track_engagement_node(state):
    """Backward-compat shim — delegates to workflows/nodes/track_engagement_node.py."""
    from agents.notification.workflows.nodes.track_engagement_node import track_engagement_node as _fn
    return _fn(state)


__all__ = ["receive_event_node", "enrich_event_context_node", "resolve_recipients_node", "classify_priority_node", "select_channel_node", "craft_message_node", "deduplicate_notification_node", "dispatch_notification_node", "track_engagement_node"]
