"""
agents/audit/core/engine.py
==============================
Audit engine — orchestrates LLM provider initialisation,
graph compilation, and the main .run() entry point.

The engine is the single point of integration between the provider
(LLM client) and the graph defined in workflows/create_graph.py.
"""
from __future__ import annotations

from shared.common import get_llm, get_tracer, get_logger

logger = get_logger(__name__)


class AuditEngine:
    """
    Main orchestration engine for the Audit agent.

    Usage
    -----
        engine = AuditEngine(agent_config={})
        state  = engine.run(raw_input="...", session_id="sess_xyz")
    """

    def __init__(self, agent_config: dict | None = None):
        self._config = agent_config or {}
        self._llm    = get_llm()                  # resolved from .env (CALL_LLM / LLM_PROVIDER)
        self._tracer = get_tracer("audit_agent")
        logger.info(f"[AuditEngine] initialised provider={type(self._llm).__name__}")

    def run(self, raw_input: str, session_id: str | None = None) -> dict:
        """
        Execute the Audit workflow graph.

        Delegates to agents/audit/graph.py::run_audit_agent().
        """
        from agents.audit.graph import run_audit_agent
        return run_audit_agent(
            raw_input=raw_input,
            session_id=session_id,
            agent_config=self._config,
        )
