"""
agents/planner/agents/specialist_agent.py
Specialist agent for planner — extends BasePlannerAgent with domain logic.
"""
from __future__ import annotations
from agents.planner.sub_agents.base_agent import BasePlannerAgent


class PlannerSpecialistAgent(BasePlannerAgent):
    """Domain specialist for the planner agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
