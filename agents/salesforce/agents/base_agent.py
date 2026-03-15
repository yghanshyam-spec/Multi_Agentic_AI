"""
agents/salesforce/agents/base_agent.py
Agent base — extends shared BaseAgent. All LLM, tracing, logging from shared/.
"""
from __future__ import annotations
from shared.agents import BaseAgent


class BaseSalesforceAgent(BaseAgent):
    """Base for all salesforce specialist implementations."""
    AGENT_NAME = "salesforce_agent"

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
