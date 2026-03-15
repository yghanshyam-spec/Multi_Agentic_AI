"""agents/audit/graph.py — Audit Agent entry-point.

Thin proxy: the full audit runner lives in agents/execution/graph.py
(all three governance agents share that file). This module re-exports
run_audit_agent so that ``from agents.audit.graph import run_audit_agent``
works, and satisfies the shared-state contract requirements.
"""
from __future__ import annotations

# ── Shared state contract — compulsory imports for all 21 agents ─────────────
from shared import (
    AuditAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

# ── Delegate to canonical implementation ─────────────────────────────────────
from agents.execution.graph import run_audit_agent  # noqa: F401 — re-export

# ── Canonical node imports ────────────────────────────────────────────────────
from agents.audit.nodes.audit_nodes import (
    listen_for_events_node, normalise_event_node, redact_pii_node,
    evaluate_policy_node, persist_audit_log_node, correlate_traces_node,
    detect_anomalies_node, generate_audit_report_node,
)
from agents.audit.workflows.nodes import (
    listen_for_events_node, normalise_event_node, redact_pii_node,
    evaluate_policy_node, persist_audit_log_node, correlate_traces_node,
    detect_anomalies_node, generate_audit_report_node,
)

# ── Convenience: direct runner using AgentType.AUDIT ─────────────────────────
def run_audit(
    all_audit_events: list = None,
    session_id: str = None,
    agent_config: dict = None,
) -> dict:
    """Wrapper that ensures AgentType.AUDIT is stamped on the base state."""
    state = make_base_state(
        "Audit all pipeline events",
        AgentType.AUDIT,
        session_id=session_id,
    )
    # ── Stamp run/correlation IDs for end-to-end Langfuse tracing ────────────
    state.setdefault("run_id", state.get("session_id", ""))
    state.setdefault("correlation_id", state.get("session_id", ""))
    state.update({
        "events_to_process":  [],
        "normalised_events":  [],
        "policy_results":     [],
        "anomalies":          [],
        "persisted_records":  [],
        "audit_report":       None,
        "compliance_score":   1.0,
        "langfuse_trace_id":  None,
        "config":             agent_config or {},
        "working_memory":     {"all_audit_events": all_audit_events or []},
    })
    result = run_audit_agent(
        all_audit_events_or_raw=all_audit_events or [],
        session_id=state["session_id"],
        agent_config=agent_config,
    )
    # Stamp AgentResponse envelope
    result["agent_response"] = dict(build_agent_response(
        result,
        payload={"result": result.get("audit_report")},
        confidence_score=result.get("working_memory", {}).get("confidence", 0.95),
    ))
    result.setdefault("audit_events", []).append(
        make_audit_event(result, "run_audit", "AGENT_COMPLETED")
    )
    return result


__all__ = ["run_audit_agent", "run_audit"]
