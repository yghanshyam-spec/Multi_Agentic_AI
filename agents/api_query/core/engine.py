"""
agents/api_query/core/engine.py
Thin engine — delegates entirely to shared infrastructure.
All LLM, tracing, and prompt management come from shared/.
"""
from __future__ import annotations
from shared.common import get_llm, get_tracer, get_logger

logger = get_logger(__name__)


class ApiQueryEngine:
    """Orchestration engine for the api_query agent."""

    def __init__(self, agent_config: dict | None = None):
        self._config = agent_config or {}
        self._llm    = get_llm()
        self._tracer = get_tracer("api_query_agent")
        logger.info(f"[ApiQueryEngine] initialised  provider={type(self._llm).__name__}")

    def run(self, raw_input: str, session_id: str | None = None) -> dict:
        from agents.api_query.graph import run_api_query_agent
        return run_api_query_agent(
            raw_input=raw_input,
            session_id=session_id,
            agent_config=self._config,
        )
