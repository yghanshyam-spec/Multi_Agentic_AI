"""
agents/reasoning/agents/specialist_agent.py
Specialist agent for reasoning — extends BaseReasoningAgent with domain logic.
"""
from __future__ import annotations
from agents.reasoning.agents.base_agent import BaseReasoningAgent


class ReasoningSpecialistAgent(BaseReasoningAgent):
    """Domain specialist for the reasoning agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
