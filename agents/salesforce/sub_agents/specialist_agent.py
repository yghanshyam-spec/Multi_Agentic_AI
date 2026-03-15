"""
agents/salesforce/agents/specialist_agent.py
Specialist agent for salesforce — extends BaseSalesforceAgent with domain logic.
"""
from __future__ import annotations
from agents.salesforce.sub_agents.base_agent import BaseSalesforceAgent


class SalesforceSpecialistAgent(BaseSalesforceAgent):
    """Domain specialist for the salesforce agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
