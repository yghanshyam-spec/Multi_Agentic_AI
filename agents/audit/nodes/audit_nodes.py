"""agents/audit/nodes/audit_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/audit/workflows/nodes/ (one file per node).
New code should import directly from agents.audit.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def listen_for_events_node(state):
    """Backward-compat shim — delegates to workflows/nodes/listen_for_events_node.py."""
    from agents.audit.workflows.nodes.listen_for_events_node import listen_for_events_node as _fn
    return _fn(state)

def normalise_event_node(state):
    """Backward-compat shim — delegates to workflows/nodes/normalise_event_node.py."""
    from agents.audit.workflows.nodes.normalise_event_node import normalise_event_node as _fn
    return _fn(state)

def redact_pii_node(state):
    """Backward-compat shim — delegates to workflows/nodes/redact_pii_node.py."""
    from agents.audit.workflows.nodes.redact_pii_node import redact_pii_node as _fn
    return _fn(state)

def evaluate_policy_node(state):
    """Backward-compat shim — delegates to workflows/nodes/evaluate_policy_node.py."""
    from agents.audit.workflows.nodes.evaluate_policy_node import evaluate_policy_node as _fn
    return _fn(state)

def persist_audit_log_node(state):
    """Backward-compat shim — delegates to workflows/nodes/persist_audit_log_node.py."""
    from agents.audit.workflows.nodes.persist_audit_log_node import persist_audit_log_node as _fn
    return _fn(state)

def correlate_traces_node(state):
    """Backward-compat shim — delegates to workflows/nodes/correlate_traces_node.py."""
    from agents.audit.workflows.nodes.correlate_traces_node import correlate_traces_node as _fn
    return _fn(state)

def detect_anomalies_node(state):
    """Backward-compat shim — delegates to workflows/nodes/detect_anomalies_node.py."""
    from agents.audit.workflows.nodes.detect_anomalies_node import detect_anomalies_node as _fn
    return _fn(state)

def generate_audit_report_node(state):
    """Backward-compat shim — delegates to workflows/nodes/generate_audit_report_node.py."""
    from agents.audit.workflows.nodes.generate_audit_report_node import generate_audit_report_node as _fn
    return _fn(state)


__all__ = ["listen_for_events_node", "normalise_event_node", "redact_pii_node", "evaluate_policy_node", "persist_audit_log_node", "correlate_traces_node", "detect_anomalies_node", "generate_audit_report_node"]
