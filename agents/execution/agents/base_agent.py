"""
agents/execution/agents/base_agent.py
==================================
Agent-specific base class for the Execution agent.

Extends shared.agents.BaseAgent — all LLM routing, tracing, and logging
are inherited from the shared layer.  Override AGENT_NAME and add any
execution-specific configuration defaults here.
"""
from __future__ import annotations
from shared.agents import BaseAgent


class BaseExecutionAgent(BaseAgent):
    """Base for all Execution specialist implementations."""

    AGENT_NAME = "execution_agent"

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
