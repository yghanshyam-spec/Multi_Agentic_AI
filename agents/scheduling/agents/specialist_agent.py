"""
agents/scheduling/agents/specialist_agent.py
Specialist agent for scheduling — extends BaseSchedulingAgent with domain logic.
"""
from __future__ import annotations
from agents.scheduling.agents.base_agent import BaseSchedulingAgent


class SchedulingSpecialistAgent(BaseSchedulingAgent):
    """Domain specialist for the scheduling agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
