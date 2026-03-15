"""
agents/execution/agents/specialist_agent.py
=====================================
Specialist agent implementation for Execution.

Extends BaseExecutionAgent with domain-specific logic and overrides.
"""
from __future__ import annotations
from agents.execution.sub_agents.base_agent import BaseExecutionAgent


class ExecutionSpecialistAgent(BaseExecutionAgent):
    """
    Domain specialist for the Execution agent.

    Add execution-specific behaviour here:
    - Custom invoke() overrides for domain formatting
    - Pre/post-processing hooks
    - Domain-specific configuration defaults
    """

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
