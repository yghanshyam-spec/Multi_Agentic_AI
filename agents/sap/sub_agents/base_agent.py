"""
agents/sap/agents/base_agent.py
Agent base — extends shared BaseAgent. All LLM, tracing, logging from shared/.
"""
from __future__ import annotations
from shared.agents import BaseAgent


class BaseSapAgent(BaseAgent):
    """Base for all sap specialist implementations."""
    AGENT_NAME = "sap_agent"

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
