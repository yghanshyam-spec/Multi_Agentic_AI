"""
agents/generator/workflows/nodes/select_template_node.py
========================================================
Node function: ``select_template_node``

Single-responsibility node — part of the Generator LangGraph workflow.
Implementation delegated to agents/generator/nodes/generator_nodes.py for
backward compatibility; split-file is the canonical import path.
"""
from __future__ import annotations
from agents.generator.nodes.generator_nodes import select_template_node

__all__ = ["select_template_node"]
