"""
agents/intent/agents/specialist_agent.py
Specialist agent for intent — extends BaseIntentAgent with domain logic.
"""
from __future__ import annotations
from agents.intent.agents.base_agent import BaseIntentAgent


class IntentSpecialistAgent(BaseIntentAgent):
    """Domain specialist for the intent agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
