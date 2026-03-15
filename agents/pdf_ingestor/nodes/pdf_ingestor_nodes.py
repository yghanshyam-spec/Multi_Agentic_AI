"""agents/pdf_ingestor/nodes/pdf_ingestor_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/pdf_ingestor/workflows/nodes/ (one file per node).
New code should import directly from agents.pdf_ingestor.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def trigger_ingestion_node(state):
    """Backward-compat shim — delegates to workflows/nodes/trigger_ingestion_node.py."""
    from agents.pdf_ingestor.workflows.nodes.trigger_ingestion_node import trigger_ingestion_node as _fn
    return _fn(state)

def extract_text_node(state):
    """Backward-compat shim — delegates to workflows/nodes/extract_text_node.py."""
    from agents.pdf_ingestor.workflows.nodes.extract_text_node import extract_text_node as _fn
    return _fn(state)

def clean_text_node(state):
    """Backward-compat shim — delegates to workflows/nodes/clean_text_node.py."""
    from agents.pdf_ingestor.workflows.nodes.clean_text_node import clean_text_node as _fn
    return _fn(state)

def classify_sections_node(state):
    """Backward-compat shim — delegates to workflows/nodes/classify_sections_node.py."""
    from agents.pdf_ingestor.workflows.nodes.classify_sections_node import classify_sections_node as _fn
    return _fn(state)

def chunk_documents_node(state):
    """Backward-compat shim — delegates to workflows/nodes/chunk_documents_node.py."""
    from agents.pdf_ingestor.workflows.nodes.chunk_documents_node import chunk_documents_node as _fn
    return _fn(state)

def embed_chunks_node(state):
    """Backward-compat shim — delegates to workflows/nodes/embed_chunks_node.py."""
    from agents.pdf_ingestor.workflows.nodes.embed_chunks_node import embed_chunks_node as _fn
    return _fn(state)

def upsert_vectors_node(state):
    """Backward-compat shim — delegates to workflows/nodes/upsert_vectors_node.py."""
    from agents.pdf_ingestor.workflows.nodes.upsert_vectors_node import upsert_vectors_node as _fn
    return _fn(state)

def audit_ingestion_node(state):
    """Backward-compat shim — delegates to workflows/nodes/audit_ingestion_node.py."""
    from agents.pdf_ingestor.workflows.nodes.audit_ingestion_node import audit_ingestion_node as _fn
    return _fn(state)


__all__ = ["trigger_ingestion_node", "extract_text_node", "clean_text_node", "classify_sections_node", "chunk_documents_node", "embed_chunks_node", "upsert_vectors_node", "audit_ingestion_node"]
