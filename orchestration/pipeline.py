"""
orchestration/pipeline.py
==========================
Generalised Orchestration Layer — use-case agnostic.

All 21 agents registered. Agent folder names follow clean naming (no _agent suffix).

Router agent flow
-----------------
The Router agent is the Layer-0 entry-point.  The pipeline builds its graph
ONCE at import time and injects the pre-compiled graph into every run_router()
call, avoiding repeated graph compilation per request::

    graph = build_router_graph()          # compile once
    result = run_router(input, graph=graph)   # invoke N times
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from shared import utc_now, new_id
from shared.langfuse_manager import get_tracer


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER GRAPH — compiled once at module load, reused for every pipeline run
# ─────────────────────────────────────────────────────────────────────────────

def _build_router_graph():
    """
    Compile the Router LangGraph once at module load.
    Returns None if langgraph is not installed (engine falls back automatically).
    """
    try:
        from agents.router.workflows.create_graph import build_router_graph
        return build_router_graph()
    except Exception:
        return None

_ROUTER_GRAPH = _build_router_graph()


# ─────────────────────────────────────────────────────────────────────────────
# AGENT REGISTRY — maps string keys to runner functions
# ─────────────────────────────────────────────────────────────────────────────

def _load_agents() -> Dict[str, Callable]:
    """Lazy-import all 21 agent runners. Allows partial availability."""
    from agents.router.core.engine import run_router
    from agents.intent.core.engine import run_intent_agent
    from agents.planner.core.engine import run_planner_agent
    from agents.workflow.core.engine import run_workflow_agent
    from agents.reasoning.core.engine import run_reasoning_agent
    from agents.generator.core.engine import run_generator_agent
    from agents.communication.core.engine import run_communication_agent
    from agents.execution.core.engine import run_execution_agent, run_hitl_agent, run_audit_agent
    from agents.translation.core.engine import run_translation_agent
    from agents.email_handler.core.engine import run_email_handler_agent
    from agents.sql.core.engine import run_sql_agent
    from agents.pdf_ingestor.core.engine import run_pdf_ingestor_agent
    from agents.vector_query.core.engine import run_vector_query_agent
    from agents.mcp_invoker.core.engine import run_mcp_invoker_agent
    from agents.salesforce.core.engine import run_salesforce_agent
    from agents.sap.core.engine import run_sap_agent
    from agents.notification.core.engine import run_notification_agent
    from agents.scheduling.core.engine import run_scheduling_agent
    from agents.api_query.core.engine import run_api_query_agent

    return {
        # ── Layer 0 — Entry ──────────────────────────────────────────────────
        "router":           run_router,
        # ── Layer 1 — Orchestration ──────────────────────────────────────────
        "intent":           run_intent_agent,
        "planner":          run_planner_agent,
        "workflow":         run_workflow_agent,
        # ── Layer 2 — Intelligence ───────────────────────────────────────────
        "reasoning":        run_reasoning_agent,
        "generator":        run_generator_agent,
        "communication":    run_communication_agent,
        "translation":      run_translation_agent,
        # ── Layer 2 — Data ───────────────────────────────────────────────────
        "sql":              run_sql_agent,
        "pdf_ingestor":     run_pdf_ingestor_agent,
        "vector_query":     run_vector_query_agent,
        "api_query":        run_api_query_agent,
        # ── Layer 2 — Integration ────────────────────────────────────────────
        "mcp_invoker":      run_mcp_invoker_agent,
        "salesforce":       run_salesforce_agent,
        "sap":              run_sap_agent,
        "email_handler":    run_email_handler_agent,
        # ── Layer 3 — Governance / Execution ────────────────────────────────
        "execution":        run_execution_agent,
        "hitl":             run_hitl_agent,
        "audit":            run_audit_agent,
        "notification":     run_notification_agent,
        "scheduling":       run_scheduling_agent,
    }


# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StepDef:
    """Single step in a use-case pipeline."""
    id:           str
    agent:        str
    label:        str
    layer:        int                            = 0
    input_fn:     Callable                       = field(default=lambda ctx, inp: (inp, {}))
    deps:         List[str]                      = field(default_factory=list)
    agent_config: Dict[str, Any]                 = field(default_factory=dict)
    optional:     bool                           = False


@dataclass
class UseCaseConfig:
    """Fully declarative use-case configuration."""
    name:          str
    description:   str                           = ""
    steps:         List[StepDef]                 = field(default_factory=list)
    global_config: Dict[str, Any]                = field(default_factory=dict)
    langfuse_tags: List[str]                     = field(default_factory=list)


@dataclass
class StepResult:
    step_id:      str
    step_label:   str
    agent:        str
    layer:        int
    status:       str
    duration_ms:  int
    key_output:   Dict[str, Any]
    full_state:   Dict[str, Any]
    error:        Optional[str]                  = None
    audit_events: List[dict]                     = field(default_factory=list)
    trace:        List[dict]                     = field(default_factory=list)


@dataclass
class PipelineResult:
    run_id:            str
    use_case:          str
    user_input:        str
    session_id:        str
    started_at:        str
    completed_at:      str
    total_duration_ms: int
    steps:             List[StepResult]
    final_output:      Dict[str, Any]
    all_audit_events:  List[dict]
    langfuse_trace_id: Optional[str]             = None


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACK TYPE
# ─────────────────────────────────────────────────────────────────────────────

StepCallback = Callable[[str, str, int, str], None]
"""Called with (step_id, label, layer, status) on each step transition."""


# ─────────────────────────────────────────────────────────────────────────────
# TOPOLOGICAL SORT
# ─────────────────────────────────────────────────────────────────────────────

def _topo_sort(steps: List[StepDef]) -> List[StepDef]:
    """Return steps in dependency-respecting execution order."""
    id_map = {s.id: s for s in steps}
    visited, ordered = set(), []

    def visit(sid: str):
        if sid in visited:
            return
        visited.add(sid)
        for dep in id_map[sid].deps:
            if dep in id_map:
                visit(dep)
        ordered.append(id_map[sid])

    for s in steps:
        visit(s.id)
    return ordered


# ─────────────────────────────────────────────────────────────────────────────
# STEP RUNNER
# ─────────────────────────────────────────────────────────────────────────────

class AgentStepRunner:
    """Runs a single StepDef and returns a StepResult."""

    def __init__(self, agents: Dict[str, Callable], session_id: str,
                 global_config: Dict[str, Any]):
        self._agents        = agents
        self._session_id    = session_id
        self._global_config = global_config

    def run(self, step: StepDef, raw_input: str,
            pipeline_ctx: Dict[str, Any]) -> Tuple[StepResult, dict]:
        fn = self._agents.get(step.agent)
        if fn is None:
            raise ValueError(f"Unknown agent '{step.agent}' in step '{step.id}'")

        merged_config = {**self._global_config, **step.agent_config}

        try:
            step_input, extra_kwargs = step.input_fn(pipeline_ctx, raw_input)
        except Exception:
            step_input, extra_kwargs = raw_input, {}

        if "agent_config" in extra_kwargs:
            merged_config = {**merged_config, **extra_kwargs.pop("agent_config")}

        # ── Inject the pre-compiled router graph for the router step ─────────
        if step.agent == "router" and _ROUTER_GRAPH is not None:
            extra_kwargs.setdefault("graph", _ROUTER_GRAPH)

        t0 = time.monotonic()
        try:
            state = fn(
                step_input,
                session_id=self._session_id,
                agent_config=merged_config,
                **extra_kwargs,
            )
            duration_ms = int((time.monotonic() - t0) * 1000)
            status = state.get("status", "COMPLETED")
        except Exception as exc:
            duration_ms = int((time.monotonic() - t0) * 1000)
            if not step.optional:
                raise
            state  = {}
            status = "FAILED"

        pipeline_ctx[step.id] = state

        return StepResult(
            step_id=step.id,
            step_label=step.label,
            agent=step.agent,
            layer=step.layer,
            status=status,
            duration_ms=duration_ms,
            key_output=_extract_key_output(step.agent, state),
            full_state=state,
            audit_events=state.get("audit_events", []),
            trace=state.get("execution_trace", []),
        ), state


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(
    use_case: UseCaseConfig,
    user_input: str,
    session_id: str = None,
    on_step: Optional[StepCallback] = None,
) -> PipelineResult:
    agents     = _load_agents()
    sid        = session_id or new_id("sess")
    run_id     = new_id("run")
    started_at = utc_now()
    t_total    = time.monotonic()

    steps_ordered    = _topo_sort(use_case.steps)
    runner           = AgentStepRunner(agents, sid, use_case.global_config)
    pipeline_ctx     : Dict[str, Any] = {}
    all_results      : List[StepResult] = []
    all_audit_events : List[dict] = []
    final_output     : Dict[str, Any] = {}

    tracer = get_tracer("orchestration")

    with tracer.trace(
        use_case.name.replace(" ", "_").lower(),
        session_id=sid,
        input=user_input[:300],
        metadata={"use_case": use_case.name, "tags": use_case.langfuse_tags},
    ) as root_trace:

        for step in steps_ordered:
            if on_step:
                on_step(step.id, step.label, step.layer, "running")

            try:
                sr, state = runner.run(step, user_input, pipeline_ctx)
                all_audit_events.extend(sr.audit_events)
                all_results.append(sr)
                final_output[step.id] = sr.key_output
                if on_step:
                    on_step(step.id, step.label, step.layer, sr.status)
            except Exception as exc:
                err_sr = StepResult(
                    step_id=step.id, step_label=step.label, agent=step.agent,
                    layer=step.layer, status="FAILED",
                    duration_ms=0, key_output={}, full_state={},
                    error=str(exc),
                )
                all_results.append(err_sr)
                if on_step:
                    on_step(step.id, step.label, step.layer, "failed")
                root_trace.update(output={"error": str(exc)})
                break

        total_ms = int((time.monotonic() - t_total) * 1000)
        root_trace.update(output={
            "steps_completed": len([r for r in all_results if r.status != "FAILED"]),
            "total_ms": total_ms,
        })

    tracer.flush()

    return PipelineResult(
        run_id=run_id,
        use_case=use_case.name,
        user_input=user_input,
        session_id=sid,
        started_at=started_at,
        completed_at=utc_now(),
        total_duration_ms=total_ms,
        steps=all_results,
        final_output=final_output,
        all_audit_events=all_audit_events,
    )


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: extract displayable key output per agent type
# ─────────────────────────────────────────────────────────────────────────────

def _extract_key_output(agent: str, state: dict) -> dict:
    extractors = {
        "router":        lambda s: {
                             "agents_activated": s.get("activated_agents", []),
                             "final_response":   (s.get("final_response") or "")[:300],
                             # also surface the structured AgentResponse envelope
                             "agent_response":   s.get("agent_response", {}),
                         },
        "intent":        lambda s: {"primary_intent": s.get("primary_intent"),
                                    "sub_tasks": len(s.get("sub_tasks", []))},
        "planner":       lambda s: {"plan_id": s.get("plan_id"),
                                    "task_count": len(s.get("task_graph", [])),
                                    "tasks": [t.get("title") for t in s.get("task_graph", [])]},
        "workflow":      lambda s: {"steps_completed": len(s.get("completed_steps", [])),
                                    "summary": (s.get("workflow_summary") or "")[:200]},
        "reasoning":     lambda s: {"conclusion": (s.get("conclusion") or {}).get("conclusion", "")[:300],
                                    "confidence": (s.get("conclusion") or {}).get("confidence", 0),
                                    "chain_steps": len(s.get("reasoning_chain", []))},
        "generator":     lambda s: {"template": s.get("template_id"),
                                    "sections": len(s.get("generated_sections", [])),
                                    "word_count": len((s.get("final_document") or "").split())},
        "communication": lambda s: {
                             "channel":        s.get("detected_channel"),
                             "dispatched":     (s.get("dispatch_result") or {}).get("status", ""),
                             "draft_response": (s.get("draft_response") or "")[:200],
                             "agent_response": s.get("agent_response", {}),
                         },
        "execution":     lambda s: {"exit_code": (s.get("execution_output") or {}).get("exit_code"),
                                    "rows_affected": (s.get("execution_output") or {}).get("rows_affected"),
                                    "report": (s.get("execution_report") or "")[:200]},
        "hitl":          lambda s: {"decision": s.get("decision_value"),
                                    "approver": s.get("approver_id"),
                                    "brief": (s.get("review_brief") or "")[:200]},
        "audit":         lambda s: {"total_events": len(s.get("normalised_events", [])),
                                    "violations": sum(len((r.get("result") or {}).get("violations", []))
                                                      for r in s.get("policy_results", [])),
                                    "compliance_score": s.get("compliance_score", 1.0)},
        "translation":   lambda s: {"source_lang": s.get("source_language"),
                                    "target_lang": s.get("target_language"),
                                    "translated": bool(s.get("final_translated_text"))},
        "email_handler": lambda s: {"subject": s.get("email_subject"),
                                    "classification": s.get("email_classification")},
        "sql":           lambda s: {"sql": (s.get("generated_sql") or "")[:150],
                                    "rows": s.get("query_result_count", 0)},
        "pdf_ingestor":  lambda s: {"pages": s.get("total_pages", 0),
                                    "chunks": s.get("total_chunks", 0)},
        "vector_query":  lambda s: {"answer": (s.get("generated_response") or "")[:200],
                                    "chunks_retrieved": len(s.get("retrieved_chunks", []))},
        "api_query":     lambda s: {"endpoint": s.get("api_endpoint"),
                                    "status": s.get("api_status_code")},
        "mcp_invoker":   lambda s: {"tool": s.get("mcp_tool_called"),
                                    "result": (s.get("mcp_tool_result") or "")[:200]},
        "salesforce":    lambda s: {"records": s.get("sf_record_count", 0),
                                    "object": s.get("sf_object_type")},
        "sap":           lambda s: {"bapi": s.get("selected_bapi"),
                                    "summary": (s.get("sap_summary") or "")[:200]},
        "notification":  lambda s: {"channel": s.get("selected_channel"),
                                    "dispatched": s.get("dispatch_result", {}).get("status", "")},
        "scheduling":    lambda s: {"summary": (s.get("scheduling_summary") or "")[:200],
                                    "event": s.get("event_subject")},
    }
    fn = extractors.get(agent)
    try:
        return fn(state) if fn else {}
    except Exception:
        return {}
