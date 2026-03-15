"""
agents/generator/workflows/nodes/generate_section_node.py
=========================================================
Node function: ``generate_section_node``

Single-responsibility node — part of the Generator LangGraph workflow.
Implementation delegated to agents/generator/nodes/generator_nodes.py for
backward compatibility; split-file is the canonical import path.
"""
from __future__ import annotations
from agents.generator.nodes.generator_nodes import generate_section_node

__all__ = ["generate_section_node"]
