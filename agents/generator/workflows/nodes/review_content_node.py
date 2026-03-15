"""
agents/generator/workflows/nodes/review_content_node.py
=======================================================
Node function: ``review_content_node``

Single-responsibility node — part of the Generator LangGraph workflow.
Implementation delegated to agents/generator/nodes/generator_nodes.py for
backward compatibility; split-file is the canonical import path.
"""
from __future__ import annotations
from agents.generator.nodes.generator_nodes import review_content_node

__all__ = ["review_content_node"]
