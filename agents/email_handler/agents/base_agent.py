"""
agents/email_handler/agents/base_agent.py
Agent base — extends shared BaseAgent. All LLM, tracing, logging from shared/.
"""
from __future__ import annotations
from shared.agents import BaseAgent


class BaseEmailHandlerAgent(BaseAgent):
    """Base for all email_handler specialist implementations."""
    AGENT_NAME = "email_handler_agent"

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
