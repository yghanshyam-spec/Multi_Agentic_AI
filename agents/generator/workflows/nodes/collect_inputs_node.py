"""
agents/generator/workflows/nodes/collect_inputs_node.py
=======================================================
Node function: ``collect_inputs_node``

Single-responsibility node — part of the Generator LangGraph workflow.
Implementation delegated to agents/generator/nodes/generator_nodes.py for
backward compatibility; split-file is the canonical import path.
"""
from __future__ import annotations
from agents.generator.nodes.generator_nodes import collect_inputs_node

__all__ = ["collect_inputs_node"]
