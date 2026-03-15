"""
agents/communication/agents/specialist_agent.py
=========================================
Specialist agent implementation for Communication.

Extends BaseCommunicationAgent with domain-specific logic and overrides.
"""
from __future__ import annotations
from shared.agents import BaseAgent as BaseCommunicationAgent  # shared base


class CommunicationSpecialistAgent(BaseCommunicationAgent):
    """
    Domain specialist for the Communication agent.

    Add communication-specific behaviour here:
    - Custom invoke() overrides for domain formatting
    - Pre/post-processing hooks
    - Domain-specific configuration defaults
    """

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
