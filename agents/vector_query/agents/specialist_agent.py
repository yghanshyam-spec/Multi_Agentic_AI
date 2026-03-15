"""
agents/vector_query/agents/specialist_agent.py
Specialist agent for vector_query — extends BaseVectorQueryAgent with domain logic.
"""
from __future__ import annotations
from agents.vector_query.agents.base_agent import BaseVectorQueryAgent


class VectorQuerySpecialistAgent(BaseVectorQueryAgent):
    """Domain specialist for the vector_query agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
