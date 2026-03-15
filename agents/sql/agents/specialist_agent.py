"""
agents/sql/agents/specialist_agent.py
Specialist agent for sql — extends BaseSqlAgent with domain logic.
"""
from __future__ import annotations
from agents.sql.agents.base_agent import BaseSqlAgent


class SqlSpecialistAgent(BaseSqlAgent):
    """Domain specialist for the sql agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
