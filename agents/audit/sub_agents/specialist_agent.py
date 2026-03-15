"""
agents/audit/agents/specialist_agent.py
=================================
Specialist agent implementation for Audit.

Extends BaseAuditAgent with domain-specific logic and overrides.
"""
from __future__ import annotations
from agents.audit.sub_agents.base_agent import BaseAuditAgent


class AuditSpecialistAgent(BaseAuditAgent):
    """
    Domain specialist for the Audit agent.

    Add audit-specific behaviour here:
    - Custom invoke() overrides for domain formatting
    - Pre/post-processing hooks
    - Domain-specific configuration defaults
    """

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
