"""agents/router/nodes/router_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/router/workflows/nodes/ (one file per node).
New code should import directly from agents.router.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def analyse_request_node(state):
    """Backward-compat shim — delegates to workflows/nodes/analyse_request_node.py."""
    from agents.router.workflows.nodes.analyse_request_node import analyse_request_node as _fn
    return _fn(state)

def monitor_load_node(state):
    """Backward-compat shim — delegates to workflows/nodes/monitor_load_node.py."""
    from agents.router.workflows.nodes.monitor_load_node import monitor_load_node as _fn
    return _fn(state)

def plan_routing_node(state):
    """Backward-compat shim — delegates to workflows/nodes/plan_routing_node.py."""
    from agents.router.workflows.nodes.plan_routing_node import plan_routing_node as _fn
    return _fn(state)

def activate_agents_node(state):
    """Backward-compat shim — delegates to workflows/nodes/activate_agents_node.py."""
    from agents.router.workflows.nodes.activate_agents_node import activate_agents_node as _fn
    return _fn(state)

def monitor_execution_node(state):
    """Backward-compat shim — delegates to workflows/nodes/monitor_execution_node.py."""
    from agents.router.workflows.nodes.monitor_execution_node import monitor_execution_node as _fn
    return _fn(state)

def collect_results_node(state):
    """Backward-compat shim — delegates to workflows/nodes/collect_results_node.py."""
    from agents.router.workflows.nodes.collect_results_node import collect_results_node as _fn
    return _fn(state)

def orchestrate_response_node(state):
    """Backward-compat shim — delegates to workflows/nodes/orchestrate_response_node.py."""
    from agents.router.workflows.nodes.orchestrate_response_node import orchestrate_response_node as _fn
    return _fn(state)


__all__ = ["analyse_request_node", "monitor_load_node", "plan_routing_node", "activate_agents_node", "monitor_execution_node", "collect_results_node", "orchestrate_response_node"]
