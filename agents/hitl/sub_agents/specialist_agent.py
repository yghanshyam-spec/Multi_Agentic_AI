"""
agents/hitl/agents/specialist_agent.py
================================
Specialist agent implementation for Hitl.

Extends BaseHitlAgent with domain-specific logic and overrides.
"""
from __future__ import annotations
from agents.hitl.sub_agents.base_agent import BaseHitlAgent


class HitlSpecialistAgent(BaseHitlAgent):
    """
    Domain specialist for the Hitl agent.

    Add hitl-specific behaviour here:
    - Custom invoke() overrides for domain formatting
    - Pre/post-processing hooks
    - Domain-specific configuration defaults
    """

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
