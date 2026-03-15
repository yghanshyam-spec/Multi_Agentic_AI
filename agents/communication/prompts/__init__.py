"""
agents/communication/prompts/__init__.py
Prompt resolution fully delegated to shared/langfuse_manager.get_prompt().
"""
from agents.communication.prompts.defaults import get_default_prompt
__all__ = ["get_default_prompt"]
