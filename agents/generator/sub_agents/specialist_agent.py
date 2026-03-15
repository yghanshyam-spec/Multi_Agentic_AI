"""
agents/generator/agents/specialist_agent.py
Specialist agent for generator — extends BaseGeneratorAgent with domain logic.
"""
from __future__ import annotations
from agents.generator.agents.base_agent import BaseGeneratorAgent


class GeneratorSpecialistAgent(BaseGeneratorAgent):
    """Domain specialist for the generator agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
