"""
agents/communication/agents/base_agent.py
Communication agent base — delegates entirely to shared.agents.BaseAgent.
"""
from __future__ import annotations
from shared.agents import BaseAgent


class BaseCommunicationAgent(BaseAgent):
    """Base for all Communication specialist implementations."""
    AGENT_NAME = "communication_agent"

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
