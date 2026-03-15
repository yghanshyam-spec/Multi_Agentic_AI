"""
agents/hitl/agents/base_agent.py
=============================
Agent-specific base class for the Hitl agent.

Extends shared.agents.BaseAgent — all LLM routing, tracing, and logging
are inherited from the shared layer.  Override AGENT_NAME and add any
hitl-specific configuration defaults here.
"""
from __future__ import annotations
from shared.agents import BaseAgent


class BaseHitlAgent(BaseAgent):
    """Base for all Hitl specialist implementations."""

    AGENT_NAME = "hitl_agent"

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
