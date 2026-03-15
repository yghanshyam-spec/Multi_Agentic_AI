"""
agents/workflow/agents/specialist_agent.py
Specialist agent for workflow — extends BaseWorkflowAgent with domain logic.
"""
from __future__ import annotations
from agents.workflow.agents.base_agent import BaseWorkflowAgent


class WorkflowSpecialistAgent(BaseWorkflowAgent):
    """Domain specialist for the workflow agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
