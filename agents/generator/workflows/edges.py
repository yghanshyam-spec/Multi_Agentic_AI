"""
agents/generator/workflows/edges.py
=====================================
Conditional routing logic for the Generator LangGraph workflow.
"""
from __future__ import annotations

def should_refine(state: dict) -> str:
    """Route to refine_content if review score is below threshold, else assemble."""
    review = state.get("review_result", {})
    if review.get("revision_needed", False):
        return "refine_content_node"
    return "assemble_document_node"
