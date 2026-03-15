"""agents/vector_query/nodes/vector_query_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/vector_query/workflows/nodes/ (one file per node).
New code should import directly from agents.vector_query.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def preprocess_query_node(state):
    """Backward-compat shim — delegates to workflows/nodes/preprocess_query_node.py."""
    from agents.vector_query.workflows.nodes.preprocess_query_node import preprocess_query_node as _fn
    return _fn(state)

def embed_query_node(state):
    """Backward-compat shim — delegates to workflows/nodes/embed_query_node.py."""
    from agents.vector_query.workflows.nodes.embed_query_node import embed_query_node as _fn
    return _fn(state)

def retrieve_chunks_node(state):
    """Backward-compat shim — delegates to workflows/nodes/retrieve_chunks_node.py."""
    from agents.vector_query.workflows.nodes.retrieve_chunks_node import retrieve_chunks_node as _fn
    return _fn(state)

def filter_chunks_node(state):
    """Backward-compat shim — delegates to workflows/nodes/filter_chunks_node.py."""
    from agents.vector_query.workflows.nodes.filter_chunks_node import filter_chunks_node as _fn
    return _fn(state)

def rerank_chunks_node(state):
    """Backward-compat shim — delegates to workflows/nodes/rerank_chunks_node.py."""
    from agents.vector_query.workflows.nodes.rerank_chunks_node import rerank_chunks_node as _fn
    return _fn(state)

def generate_response_node(state):
    """Backward-compat shim — delegates to workflows/nodes/generate_response_node.py."""
    from agents.vector_query.workflows.nodes.generate_response_node import generate_response_node as _fn
    return _fn(state)

def check_faithfulness_node(state):
    """Backward-compat shim — delegates to workflows/nodes/check_faithfulness_node.py."""
    from agents.vector_query.workflows.nodes.check_faithfulness_node import check_faithfulness_node as _fn
    return _fn(state)

def update_memory_node(state):
    """Backward-compat shim — delegates to workflows/nodes/update_memory_node.py."""
    from agents.vector_query.workflows.nodes.update_memory_node import update_memory_node as _fn
    return _fn(state)


__all__ = ["preprocess_query_node", "embed_query_node", "retrieve_chunks_node", "filter_chunks_node", "rerank_chunks_node", "generate_response_node", "check_faithfulness_node", "update_memory_node"]
