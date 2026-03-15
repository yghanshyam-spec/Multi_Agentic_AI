"""
agents/reasoning/agents/base_agent.py
Agent base — extends shared BaseAgent. All LLM, tracing, logging from shared/.
"""
from __future__ import annotations
from shared.agents import BaseAgent


class BaseReasoningAgent(BaseAgent):
    """Base for all reasoning specialist implementations."""
    AGENT_NAME = "reasoning_agent"

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
