"""
agents/mcp_invoker/agents/specialist_agent.py
Specialist agent for mcp_invoker — extends BaseMcpInvokerAgent with domain logic.
"""
from __future__ import annotations
from agents.mcp_invoker.sub_agents.base_agent import BaseMcpInvokerAgent


class McpInvokerSpecialistAgent(BaseMcpInvokerAgent):
    """Domain specialist for the mcp_invoker agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
