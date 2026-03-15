"""
agents/execution/core/engine.py
==============================
Execution engine — orchestrates LLM provider initialisation,
graph compilation, and the main .run() entry point.

The engine is the single point of integration between the provider
(LLM client) and the graph defined in workflows/create_graph.py.
"""
from __future__ import annotations

from shared.common import get_llm, get_tracer, get_logger

logger = get_logger(__name__)


class ExecutionEngine:
    """
    Main orchestration engine for the Execution agent.

    Usage
    -----
        engine = ExecutionEngine(agent_config={})
        state  = engine.run(raw_input="...", session_id="sess_xyz")
    """

    def __init__(self, agent_config: dict | None = None):
        self._config = agent_config or {}
        self._llm    = get_llm()                  # resolved from .env (CALL_LLM / LLM_PROVIDER)
        self._tracer = get_tracer("execution_agent")
        logger.info(f"[ExecutionEngine] initialised provider={type(self._llm).__name__}")

    def run(self, raw_input: str, session_id: str | None = None) -> dict:
        """
        Execute the Execution workflow graph.

        Delegates to agents/execution/graph.py::run_execution_agent().
        """
        from agents.execution.graph import run_execution_agent
        return run_execution_agent(
            raw_input=raw_input,
            session_id=session_id,
            agent_config=self._config,
        )
