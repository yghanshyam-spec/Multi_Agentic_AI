"""
agents/router/agents/specialist_agent.py
Specialist agent for router — extends BaseRouterAgent with domain logic.
"""
from __future__ import annotations
from agents.router.sub_agents.base_agent import BaseRouterAgent


class RouterSpecialistAgent(BaseRouterAgent):
    """Domain specialist for the router agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
