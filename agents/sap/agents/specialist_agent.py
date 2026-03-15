"""
agents/sap/agents/specialist_agent.py
Specialist agent for sap — extends BaseSapAgent with domain logic.
"""
from __future__ import annotations
from agents.sap.agents.base_agent import BaseSapAgent


class SapSpecialistAgent(BaseSapAgent):
    """Domain specialist for the sap agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
