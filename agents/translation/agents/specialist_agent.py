"""
agents/translation/agents/specialist_agent.py
Specialist agent for translation — extends BaseTranslationAgent with domain logic.
"""
from __future__ import annotations
from agents.translation.agents.base_agent import BaseTranslationAgent


class TranslationSpecialistAgent(BaseTranslationAgent):
    """Domain specialist for the translation agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
