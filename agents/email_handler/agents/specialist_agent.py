"""
agents/email_handler/agents/specialist_agent.py
Specialist agent for email_handler — extends BaseEmailHandlerAgent with domain logic.
"""
from __future__ import annotations
from agents.email_handler.agents.base_agent import BaseEmailHandlerAgent


class EmailHandlerSpecialistAgent(BaseEmailHandlerAgent):
    """Domain specialist for the email_handler agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
