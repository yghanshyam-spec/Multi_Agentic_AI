"""
agents/router/core/engine.py
==============================
Router Agent engine — entry point called by the pipeline.

Flow (as required by pipeline.py):
  1. pipeline calls build_router_graph() from create_graph.py to compile the graph once.
  2. pipeline calls run_router(raw_input, ..., graph=compiled_graph) to execute it.
  3. run_router invokes the graph with RouterAgentState, then wraps the final
     state into an AgentResponse and returns the full state dict.

Tracing: shared.langfuse_manager only — no local langfuse_client or prompt_manager.
"""
from __future__ import annotations

from shared.common import (
    get_llm, get_tracer, get_logger,
    AgentType, ExecutionStatus,
    make_base_state, build_agent_response, make_audit_event,
)
from shared.state import RouterAgentState

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# ENGINE CLASS  (lightweight wrapper kept for compatibility)
# ─────────────────────────────────────────────────────────────────────────────

class RouterEngine:
    """
    Thin orchestration engine for the Router agent.

    Typical use via pipeline::

        from agents.router.workflows.create_graph import build_router_graph
        from agents.router.core.engine import run_router

        graph = build_router_graph()
        result = run_router(raw_input, graph=graph)
    """

    def __init__(self, agent_config: dict | None = None):
        self._config  = agent_config or {}
        self._llm     = get_llm()
        self._tracer  = get_tracer("router_agent")
        self._graph   = None           # lazily compiled on first call
        logger.info(f"[RouterEngine] initialised  provider={type(self._llm).__name__}")

    def run(self, raw_input: str, session_id: str | None = None) -> dict:
        """Build graph on first call, then delegate to run_router()."""
        if self._graph is None:
            from agents.router.workflows.create_graph import build_router_graph
            self._graph = build_router_graph()
        return run_router(
            raw_input=raw_input,
            session_id=session_id,
            agent_config=self._config,
            graph=self._graph,
        )


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC RUNNER  — called directly by pipeline.py
# ─────────────────────────────────────────────────────────────────────────────

def run_router(
    raw_input: str,
    session_id: str = None,
    partial_results: list = None,
    agent_config: dict = None,
    graph=None,                     # pre-built compiled LangGraph (from build_router_graph)
) -> dict:
    """
    Run the Router Agent end-to-end.

    Parameters
    ----------
    raw_input       : Natural-language request from the user / pipeline.
    session_id      : Optional session identifier; auto-generated if absent.
    partial_results : Any upstream results to seed the state with.
    agent_config    : Runtime overrides — prompts, agent_registry, etc.
    graph           : Pre-compiled LangGraph returned by build_router_graph().
                      If not provided, a fresh graph is compiled on-the-fly.

    Returns
    -------
    dict  — the final RouterAgentState with ``agent_response`` set to an
            AgentResponse envelope built from the orchestrate_response_node output.
    """
    # ── 1. Build initial RouterAgentState ────────────────────────────────────
    state: dict = make_base_state(raw_input, AgentType.ROUTER, session_id=session_id)
    state.update({
        "required_agents":  [],
        "parallel_safe":    False,
        "priority":         "medium",
        "load_metrics":     {},
        "routing_plan":     None,
        "activated_agents": [],
        "agent_results":    [],
        "final_response":   None,
        "partial_results":  partial_results or [],
        "config":           agent_config or {},
    })

    # ── 2. Compile graph if not supplied ─────────────────────────────────────
    if graph is None:
        from agents.router.workflows.create_graph import build_router_graph
        graph = build_router_graph()

    # ── 3. Trace the whole workflow via shared.langfuse_manager ──────────────
    tracer = get_tracer("router_agent")
    with tracer.trace(
        "router_workflow",
        session_id=state["session_id"],
        input=raw_input[:200],
        metadata={
            "run_id":         state.get("run_id", ""),
            "correlation_id": state.get("correlation_id", ""),
        },
    ):
        if graph is not None:
            # ── 4a. Execute via compiled LangGraph ────────────────────────────
            try:
                final_state = graph.invoke(
                    state,
                    config={"configurable": {"thread_id": state["session_id"]}},
                )
                state = dict(final_state)
            except Exception as exc:
                logger.error(f"[run_router] LangGraph invocation failed: {exc}")
                state = _run_nodes_directly(state)
        else:
            # ── 4b. Fallback: run nodes directly (LangGraph not installed) ───
            state = _run_nodes_directly(state)

    tracer.flush()

    # ── 5. Build AgentResponse envelope ──────────────────────────────────────
    # orchestrate_response_node already sets agent_response on the state; we
    # re-build it here to guarantee the standard AgentResponse TypedDict is
    # always present regardless of which execution path was taken above.
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={
            "final_response":   state.get("final_response"),
            "activated_agents": state.get("activated_agents", []),
            "routing_plan":     state.get("routing_plan", {}),
        },
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))

    # ── 6. Terminal audit event ───────────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_router", "AGENT_COMPLETED")
    )

    return state


# ─────────────────────────────────────────────────────────────────────────────
# FALLBACK: imperative node execution (LangGraph not installed)
# ─────────────────────────────────────────────────────────────────────────────

def _run_nodes_directly(state: dict) -> dict:
    """Execute all seven router nodes imperatively without LangGraph."""
    from agents.router.workflows.nodes import (
        analyse_request_node,
        monitor_load_node,
        plan_routing_node,
        activate_agents_node,
        monitor_execution_node,
        collect_results_node,
        orchestrate_response_node,
    )
    state = {**state, **analyse_request_node(state)}
    state = {**state, **monitor_load_node(state)}
    state = {**state, **plan_routing_node(state)}
    state = {**state, **activate_agents_node(state)}
    state = {**state, **monitor_execution_node(state)}
    state = {**state, **collect_results_node(state)}
    state = {**state, **orchestrate_response_node(state)}
    return state
