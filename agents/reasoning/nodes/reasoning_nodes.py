"""agents/reasoning/nodes/reasoning_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/reasoning/workflows/nodes/ (one file per node).
New code should import directly from agents.reasoning.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def frame_problem_node(state):
    """Backward-compat shim — delegates to workflows/nodes/frame_problem_node.py."""
    from agents.reasoning.workflows.nodes.frame_problem_node import frame_problem_node as _fn
    return _fn(state)

def generate_hypotheses_node(state):
    """Backward-compat shim — delegates to workflows/nodes/generate_hypotheses_node.py."""
    from agents.reasoning.workflows.nodes.generate_hypotheses_node import generate_hypotheses_node as _fn
    return _fn(state)

def call_tool_node(state):
    """Backward-compat shim — delegates to workflows/nodes/call_tool_node.py."""
    from agents.reasoning.workflows.nodes.call_tool_node import call_tool_node as _fn
    return _fn(state)

def evaluate_evidence_node(state):
    """Backward-compat shim — delegates to workflows/nodes/evaluate_evidence_node.py."""
    from agents.reasoning.workflows.nodes.evaluate_evidence_node import evaluate_evidence_node as _fn
    return _fn(state)

def chain_of_thought_node(state):
    """Backward-compat shim — delegates to workflows/nodes/chain_of_thought_node.py."""
    from agents.reasoning.workflows.nodes.chain_of_thought_node import chain_of_thought_node as _fn
    return _fn(state)

def synthesise_conclusion_node(state):
    """Backward-compat shim — delegates to workflows/nodes/synthesise_conclusion_node.py."""
    from agents.reasoning.workflows.nodes.synthesise_conclusion_node import synthesise_conclusion_node as _fn
    return _fn(state)

def validate_reasoning_node(state):
    """Backward-compat shim — delegates to workflows/nodes/validate_reasoning_node.py."""
    from agents.reasoning.workflows.nodes.validate_reasoning_node import validate_reasoning_node as _fn
    return _fn(state)


__all__ = ["frame_problem_node", "generate_hypotheses_node", "call_tool_node", "evaluate_evidence_node", "chain_of_thought_node", "synthesise_conclusion_node", "validate_reasoning_node"]
