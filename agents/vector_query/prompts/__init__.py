"""
agents/vector_query/prompts/__init__.py
Prompt resolution is handled by shared/langfuse_manager.get_prompt().
The defaults.py in this folder provides built-in fallback strings.
"""
from agents.vector_query.prompts.defaults import get_default_prompt
__all__ = ["get_default_prompt"]
