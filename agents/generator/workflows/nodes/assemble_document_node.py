"""
agents/generator/workflows/nodes/assemble_document_node.py
==========================================================
Node function: ``assemble_document_node``

Single-responsibility node — part of the Generator LangGraph workflow.
Implementation delegated to agents/generator/nodes/generator_nodes.py for
backward compatibility; split-file is the canonical import path.
"""
from __future__ import annotations
from agents.generator.nodes.generator_nodes import assemble_document_node

__all__ = ["assemble_document_node"]
