"""
agents/router/workflows/create_graph.py
=========================================
LangGraph graph assembly for the Router agent.

The graph is defined here and compiled once.  Individual node functions
live in workflows/nodes/ — one file per node.

Usage
-----
    from agents.router.workflows.create_graph import build_router_graph
    graph = build_router_graph()
    result = graph.invoke(initial_state)
"""
from __future__ import annotations

try:
    from langgraph.graph import StateGraph, END
    _LG = True
except ImportError:
    _LG = False


def build_router_graph():
    """
    Assemble and compile the Router LangGraph workflow.

    Node functions are imported from workflows/nodes/.
    Returns a compiled graph, or None if LangGraph is not installed.
    """
    if not _LG:
        return None

    # Import all node functions from their individual files
    # from agents.router.workflows.nodes.my_node import my_node_fn

    # Build graph (populate with actual nodes for this agent)
    from shared import BaseAgentState
    g = StateGraph(dict)

    # Example: g.add_node("my_node", my_node_fn)
    # g.set_entry_point("my_node")
    # g.add_edge("my_node", END)

    return g.compile()
