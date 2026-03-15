"""
agents/api_query/agents/specialist_agent.py
Specialist agent for api_query — extends BaseApiQueryAgent with domain logic.
"""
from __future__ import annotations
from agents.api_query.sub_agents.base_agent import BaseApiQueryAgent


class ApiQuerySpecialistAgent(BaseApiQueryAgent):
    """Domain specialist for the api_query agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
