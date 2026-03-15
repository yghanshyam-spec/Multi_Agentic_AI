"""
agents/sap/core/engine.py
Thin engine — delegates entirely to shared infrastructure.
All LLM, tracing, and prompt management come from shared/.
"""
from __future__ import annotations
from shared.common import get_llm, get_tracer, get_logger

logger = get_logger(__name__)


class SapEngine:
    """Orchestration engine for the sap agent."""

    def __init__(self, agent_config: dict | None = None):
        self._config = agent_config or {}
        self._llm    = get_llm()
        self._tracer = get_tracer("sap_agent")
        logger.info(f"[SapEngine] initialised  provider={type(self._llm).__name__}")

    def run(self, raw_input: str, session_id: str | None = None) -> dict:
        from agents.sap.graph import run_sap_agent
        return run_sap_agent(
            raw_input=raw_input,
            session_id=session_id,
            agent_config=self._config,
        )
