"""
agents/generator/workflows/nodes/plan_content_node.py
=====================================================
Node function: ``plan_content_node``

Single-responsibility node — part of the Generator LangGraph workflow.
Implementation delegated to agents/generator/nodes/generator_nodes.py for
backward compatibility; split-file is the canonical import path.
"""
from __future__ import annotations
from agents.generator.nodes.generator_nodes import plan_content_node

__all__ = ["plan_content_node"]
