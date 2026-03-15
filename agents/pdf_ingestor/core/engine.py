"""
agents/pdf_ingestor/core/engine.py
Thin engine — delegates entirely to shared infrastructure.
All LLM, tracing, and prompt management come from shared/.
"""
from __future__ import annotations
from shared.common import get_llm, get_tracer, get_logger

logger = get_logger(__name__)


class PdfIngestorEngine:
    """Orchestration engine for the pdf_ingestor agent."""

    def __init__(self, agent_config: dict | None = None):
        self._config = agent_config or {}
        self._llm    = get_llm()
        self._tracer = get_tracer("pdf_ingestor_agent")
        logger.info(f"[PdfIngestorEngine] initialised  provider={type(self._llm).__name__}")

    def run(self, raw_input: str, session_id: str | None = None) -> dict:
        from agents.pdf_ingestor.graph import run_pdf_ingestor_agent
        return run_pdf_ingestor_agent(
            raw_input=raw_input,
            session_id=session_id,
            agent_config=self._config,
        )
