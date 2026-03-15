"""agents/translation/nodes/translation_nodes.py
Backward-compatibility shim.
Canonical implementation: agents/translation/workflows/nodes/ (one file per node).
New code should import directly from agents.translation.workflows.nodes.
"""
from __future__ import annotations

# Lazy-import shims — avoids circular imports while preserving backward compat.

def detect_language_node(state):
    """Backward-compat shim — delegates to workflows/nodes/detect_language_node.py."""
    from agents.translation.workflows.nodes.detect_language_node import detect_language_node as _fn
    return _fn(state)

def load_glossary_node(state):
    """Backward-compat shim — delegates to workflows/nodes/load_glossary_node.py."""
    from agents.translation.workflows.nodes.load_glossary_node import load_glossary_node as _fn
    return _fn(state)

def preprocess_text_node(state):
    """Backward-compat shim — delegates to workflows/nodes/preprocess_text_node.py."""
    from agents.translation.workflows.nodes.preprocess_text_node import preprocess_text_node as _fn
    return _fn(state)

def translate_node(state):
    """Backward-compat shim — delegates to workflows/nodes/translate_node.py."""
    from agents.translation.workflows.nodes.translate_node import translate_node as _fn
    return _fn(state)

def back_translate_node(state):
    """Backward-compat shim — delegates to workflows/nodes/back_translate_node.py."""
    from agents.translation.workflows.nodes.back_translate_node import back_translate_node as _fn
    return _fn(state)

def score_quality_node(state):
    """Backward-compat shim — delegates to workflows/nodes/score_quality_node.py."""
    from agents.translation.workflows.nodes.score_quality_node import score_quality_node as _fn
    return _fn(state)

def format_locale_node(state):
    """Backward-compat shim — delegates to workflows/nodes/format_locale_node.py."""
    from agents.translation.workflows.nodes.format_locale_node import format_locale_node as _fn
    return _fn(state)


__all__ = ["detect_language_node", "load_glossary_node", "preprocess_text_node", "translate_node", "back_translate_node", "score_quality_node", "format_locale_node"]
