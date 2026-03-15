"""agents/hitl/core/engine.py — HITL engine (delegates to execution.graph)."""
from __future__ import annotations
from shared.common import get_llm, get_tracer, get_logger
logger = get_logger(__name__)

class HitlEngine:
    def __init__(self, agent_config=None):
        self._config = agent_config or {}
        self._llm    = get_llm()
        self._tracer = get_tracer("hitl_agent")
        logger.info(f"[HitlEngine] initialised provider={type(self._llm).__name__}")
    def run(self, raw_input, session_id=None):
        from agents.execution.graph import run_hitl_agent
        return run_hitl_agent(raw_input=raw_input, session_id=session_id, agent_config=self._config)
