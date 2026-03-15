"""
agents/router/graph.py
======================
Layer 0 — Router Agent  (formerly Scheduler)

Renamed from "scheduler" to "router" because this agent's core responsibility
is intelligent request routing: it analyses incoming requests, checks agent
load, plans the optimal routing strategy, activates the right agents, monitors
execution, collects results, and synthesises the final orchestrated response.
"Router" communicates this purpose more precisely than "Scheduler".

Sub-folder structure:
    agents/router/
    ├── graph.py               ← THIS FILE — LangGraph entry-point
    ├── nodes/
    │   └── router_nodes.py    ← All 6 node functions (full logic here)
    ├── tools/
    │   └── load_monitor.py    ← LoadMonitor tool (per-agent health metrics)
    ├── prompts/
    │   └── defaults.py        ← Built-in prompt defaults
    ├── schemas/
    │   └── state.py           ← RouterAgentState alias
    ├── config/                ← Consumer-supplied YAML configs land here
    └── tests/                 ← Agent-specific unit tests

Prompt / Config injection pattern (consumer -> agent):
    All prompts are resolved via shared.langfuse_manager.get_prompt():
      1. Langfuse registry  (if LANGFUSE_PUBLIC_KEY / SECRET_KEY are set)
      2. state["config"]["prompts"]["<key>"]  (consumer use-case override)
      3. agents/router/prompts/defaults.py  (built-in fallback)

Langfuse observability:
    Every LLM call is logged via shared.langfuse_manager.log_llm_call().
    Full traces are created by get_tracer() wrapping run_router().
"""
from __future__ import annotations

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    _LG_AVAILABLE = True
except ImportError:
    _LG_AVAILABLE = False

from shared import (
    SchedulerAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)
from shared.langfuse_manager import get_tracer

from agents.router.nodes.router_nodes import (
    analyse_request_node,
    monitor_load_node,
    plan_routing_node,
    activate_agents_node,
    monitor_execution_node,
    collect_results_node,
    orchestrate_response_node,
)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/router/nodes/ location is preserved for backward compatibility.
from agents.router.workflows.nodes import (
    analyse_request_node, monitor_load_node, plan_routing_node, activate_agents_node, monitor_execution_node, collect_results_node, orchestrate_response_node,
)



def build_router_graph():
    """Compile the Router Agent LangGraph StateGraph."""
    if not _LG_AVAILABLE:
        return None
    graph = StateGraph(RouterAgentState)
    graph.add_node("analyse_request_node",      analyse_request_node)
    graph.add_node("monitor_load_node",         monitor_load_node)
    graph.add_node("plan_routing_node",         plan_routing_node)
    graph.add_node("activate_agents_node",      activate_agents_node)
    graph.add_node("monitor_execution_node",    monitor_execution_node)
    graph.add_node("collect_results_node",      collect_results_node)
    graph.add_node("orchestrate_response_node", orchestrate_response_node)
    graph.set_entry_point("analyse_request_node")
    graph.add_edge("analyse_request_node",    "monitor_load_node")
    graph.add_edge("monitor_load_node",       "plan_routing_node")
    graph.add_edge("plan_routing_node",       "activate_agents_node")
    graph.add_edge("activate_agents_node",    "monitor_execution_node")
    graph.add_edge("monitor_execution_node",  "collect_results_node")
    graph.add_edge("collect_results_node",    "orchestrate_response_node")
    graph.add_edge("orchestrate_response_node", END)
    return graph.compile(checkpointer=MemorySaver())


def run_router(
    raw_input: str,
    session_id: str = None,
    partial_results: list = None,
    agent_config: dict = None,
) -> dict:
    """
    Run the Router Agent.
    agent_config keys:
        "prompts"        — prompt overrides (keyed by prompt name)
        "agent_registry" — list of available agent names
    """
    from shared import make_base_state
    state = make_base_state(raw_input, AgentType.ROUTER, session_id=session_id)
    state.update({
        "partial_results":  partial_results or [],
        "load_metrics":     {},
        "routing_plan":     None,
        "activated_agents": [],
        "agent_results":    [],
        "final_response":   None,
        "required_agents":  [],
        "parallel_safe":    False,
        "priority":         "medium",
        "config":           agent_config or {},
    })

    tracer = get_tracer("router_agent")
    with tracer.trace("router_workflow", session_id=state["session_id"],
                      input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        state = {**state, **analyse_request_node(state)}
        state = {**state, **monitor_load_node(state)}
        state = {**state, **plan_routing_node(state)}
        state = {**state, **activate_agents_node(state)}
        state = {**state, **monitor_execution_node(state)}
        state = {**state, **collect_results_node(state)}
        state = {**state, **orchestrate_response_node(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("final_response")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_router", "AGENT_COMPLETED")
    )
    return state
# backward-compat alias
run_scheduler = run_router
