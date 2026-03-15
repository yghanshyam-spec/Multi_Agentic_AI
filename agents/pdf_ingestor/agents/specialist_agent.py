"""
agents/pdf_ingestor/agents/specialist_agent.py
Specialist agent for pdf_ingestor — extends BasePdfIngestorAgent with domain logic.
"""
from __future__ import annotations
from agents.pdf_ingestor.agents.base_agent import BasePdfIngestorAgent


class PdfIngestorSpecialistAgent(BasePdfIngestorAgent):
    """Domain specialist for the pdf_ingestor agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
