"""
agents/mcp_invoker/agents/base_agent.py
Agent base — extends shared BaseAgent. All LLM, tracing, logging from shared/.
"""
from __future__ import annotations
from shared.agents import BaseAgent


class BaseMcpInvokerAgent(BaseAgent):
    """Base for all mcp_invoker specialist implementations."""
    AGENT_NAME = "mcp_invoker_agent"

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
