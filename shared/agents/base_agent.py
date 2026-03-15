"""
shared/agents/base_agent.py
============================
Universal base class for all agent implementations in the accelerator.

All per-agent base_agent.py files in agents/<name>/agents/ extend this class,
adding only agent-specific configuration keys and domain defaults.

Design
------
- LLM is obtained through shared/llm_factory.py (CALL_LLM / LLM_PROVIDER in .env)
- Tracing is obtained through shared/langfuse_manager.py (LANGFUSE_ENABLED in .env)
- No LLM instantiation, logging, or tracing happens outside of shared/

Usage (from a specialist agent)
--------------------------------
    from shared.agents import BaseAgent

    class ReasoningSpecialistAgent(BaseAgent):
        AGENT_NAME = "reasoning_agent"

        def __init__(self, agent_config=None):
            super().__init__(agent_config)
            # add reasoning-specific defaults here
"""
from __future__ import annotations

from shared.llm_factory import get_llm, call_llm
from shared.langfuse_manager import get_tracer, get_prompt, log_llm_call
from shared.utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent:
    """
    Abstract base for every agent specialist implementation.

    Attributes
    ----------
    AGENT_NAME : str
        Override in subclass to set the agent identifier used in traces and logs.

    Parameters
    ----------
    agent_config : dict | None
        Per-agent runtime configuration (from UseCaseConfig or direct invocation).
        Merged with defaults at run-time by AgentStepRunner.
    temperature : float | None
        Optional LLM temperature override. Falls back to LLM_TEMPERATURE in .env.
    max_tokens : int | None
        Optional max-tokens override. Falls back to LLM_MAX_TOKENS in .env.
    """

    AGENT_NAME: str = "base_agent"

    def __init__(
        self,
        agent_config: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> None:
        self._config  = agent_config or {}
        self._llm     = get_llm(temperature=temperature, max_tokens=max_tokens)
        self._tracer  = get_tracer(self.AGENT_NAME)
        self._logger  = get_logger(f"agents.{self.AGENT_NAME}")

    # ── Core invocation ──────────────────────────────────────────────────────

    def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        node_hint: str = "",
    ) -> dict:
        """
        Invoke the LLM and return a parsed dict result.

        Routes through shared call_llm() — never calls llm.invoke() directly.
        """
        return call_llm(
            self._llm,
            system_prompt,
            user_prompt,
            node_hint=node_hint or self.AGENT_NAME,
        )

    def log_generation(
        self,
        node_name: str,
        model: str,
        prompt: str,
        response: str,
        session_id: str = "",
        token_usage: dict | None = None,
    ) -> None:
        """Log an LLM generation event to Langfuse (no-op if disabled)."""
        log_llm_call(
            agent_name=self.AGENT_NAME,
            node_name=node_name,
            model=model,
            prompt=prompt,
            response=response,
            session_id=session_id,
            token_usage=token_usage,
        )

    def get_prompt(self, key: str, fallback: str = "", **template_vars) -> str:
        """
        Resolve a prompt via the 3-tier registry:
        Langfuse → consumer override → built-in fallback.
        """
        return get_prompt(
            key,
            agent_name=self.AGENT_NAME,
            fallback=fallback,
            **template_vars,
        )

    # ── Config helpers ───────────────────────────────────────────────────────

    def cfg(self, *keys, default=None):
        """Deep-get from agent_config. cfg('sap', 'module') -> config['sap']['module']."""
        val = self._config
        for k in keys:
            if not isinstance(val, dict):
                return default
            val = val.get(k, default)
        return val

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} agent={self.AGENT_NAME} llm={type(self._llm).__name__}>"
