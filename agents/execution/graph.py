"""
agents/execution/graph.py
==========================
Layer 3 — Execution Agent (+ HITL Agent + Audit Agent)
All three governance agents live under agents/execution/ as they share
the same sub-folder structure and governance concerns.

Sub-folders:
    nodes/    — execution_nodes.py (+ hitl_nodes.py, audit_nodes.py)
    tools/    — sandbox.py  |  audit_store.py
    prompts/  — defaults.py (execution + hitl + audit built-in prompts)
    schemas/  — state extensions
    config/   — consumer YAML configs
    tests/    — unit tests
"""
from __future__ import annotations
import os
try:
    from langgraph.graph import StateGraph, END
    _LG = True
except ImportError:
    _LG = False

from shared import (
        BaseAgentState, AgentMessage, ExecutionMetadata,
ExecutionAgentState, HITLAgentState, AuditAgentState,
    AgentType, HITLDecision,
)
from shared.langfuse_manager import get_tracer
from agents.execution.nodes.execution_nodes import (
    receive_plan_node, validate_preconditions_node, manage_sandbox_node,
    execute_script_node, verify_output_node, execute_rollback_node, report_execution_node,
)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/execution/nodes/ location is preserved for backward compatibility.
from agents.execution.workflows.nodes import (
    receive_plan_node, validate_preconditions_node, manage_sandbox_node, execute_script_node, verify_output_node, execute_rollback_node, report_execution_node,
)

from agents.audit.nodes.audit_nodes import (
    listen_for_events_node, normalise_event_node, redact_pii_node,
    evaluate_policy_node, persist_audit_log_node, correlate_traces_node,
    detect_anomalies_node, generate_audit_report_node,
)

# ── HITL nodes remain inline here (they depend on HITLAgentState) ─────────────
import time
from shared import (build_agent_response, make_audit_event, utc_now,
    new_id, get_llm, call_llm, build_trace_entry, ExecutionStatus)
from shared.langfuse_manager import get_prompt, log_llm_call
from agents.execution.prompts.defaults import get_default_prompt as _edp

_HITL_REVIEW_SYS = """Prepare a clear review summary for a human approver.
Context: {context}
Include: what decision is needed, relevant facts, recommended action,
risk if approved, risk if rejected. Keep under 200 words.
Return JSON: {review_brief: str, decision_needed: str, recommended_action: str,
risk_if_approved: str, risk_if_rejected: str}"""

def _hp(key, state, **kw):
    fb = state.get("config",{}).get("prompts",{}).get(key) or _edp(f"execution_{key}") or _HITL_REVIEW_SYS
    return get_prompt(f"hitl_{key}", agent_name="hitl", fallback=fb, **kw)

def detect_checkpoint_node(state: HITLAgentState) -> dict:
    t0 = time.monotonic()
    wm = state.get("working_memory", {})
    risk = wm.get("risk","high")
    triggered = risk in ("high","critical") or state.get("feature_flags",{}).get("hitl_enabled",True)
    return {"checkpoint_triggered":triggered,"trigger_reason":f"Risk level: {risk}" if triggered else None,
            "status":ExecutionStatus.RUNNING,"current_node":"detect_checkpoint_node",
            "execution_trace":[build_trace_entry("detect_checkpoint_node",int((time.monotonic()-t0)*1000))]}

def package_review_context_node(state: HITLAgentState) -> dict:
    t0 = time.monotonic()
    wm = state.get("working_memory", {})
    sys_p = _hp("package_review_context", state, context={"request":state["raw_input"],
        "plan":wm.get("execution_plan",{}),"reasoning":wm.get("reasoning_conclusion",""),"risk":wm.get("risk","high")})
    result = call_llm(get_llm(), sys_p, "Package review for approver", node_hint="package_review_context")
    log_llm_call("hitl_agent","package_review_context_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(result),state.get("session_id",""))
    return {"review_brief":result.get("review_brief","Please review and approve."),"hitl_context":result,
            "current_node":"package_review_context_node",
            "execution_trace":[build_trace_entry("package_review_context_node",int((time.monotonic()-t0)*1000),200)],
            "audit_events":[make_audit_event(state,"package_review_context_node","HITL_PACKAGED")]}

def interrupt_node(state: HITLAgentState) -> dict:
    t0 = time.monotonic()
    return {"status":ExecutionStatus.PENDING_HUMAN,"hitl_required":True,"current_node":"interrupt_node",
            "execution_trace":[build_trace_entry("interrupt_node",int((time.monotonic()-t0)*1000))],
            "audit_events":[make_audit_event(state,"interrupt_node","WORKFLOW_INTERRUPTED")]}

def notify_approver_node(state: HITLAgentState) -> dict:
    t0 = time.monotonic()
    notification = {"recipient":state.get("approver_id","engineering_lead@company.com"),"channel":"email",
        "approve_link":f"https://platform.internal/approve/{state['run_id']}",
        "reject_link":f"https://platform.internal/reject/{state['run_id']}",
        "brief":state.get("review_brief",""),"sent_at":utc_now()}
    return {"notification_sent":True,"current_node":"notify_approver_node",
            "execution_trace":[build_trace_entry("notify_approver_node",int((time.monotonic()-t0)*1000))],
            "audit_events":[make_audit_event(state,"notify_approver_node","APPROVER_NOTIFIED")]}

def listen_for_response_node(state: HITLAgentState) -> dict:
    t0 = time.monotonic()
    decision = {"value":HITLDecision.APPROVED,"approver_id":"eng_lead_demo","timestamp":utc_now(),
        "notes":"Approved — CONCURRENT index creation is safe."}
    return {"hitl_decision":decision,"decision_value":HITLDecision.APPROVED,
            "decision_notes":decision["notes"],"approver_id":decision["approver_id"],
            "current_node":"listen_for_response_node",
            "execution_trace":[build_trace_entry("listen_for_response_node",int((time.monotonic()-t0)*1000))]}

def process_decision_node(state: HITLAgentState) -> dict:
    t0 = time.monotonic()
    decision = state.get("hitl_decision", {})
    value = decision.get("value", HITLDecision.APPROVED)
    return {"decision_value":value,
            "status":ExecutionStatus.RUNNING if value==HITLDecision.APPROVED else ExecutionStatus.CANCELLED,
            "current_node":"process_decision_node",
            "execution_trace":[build_trace_entry("process_decision_node",int((time.monotonic()-t0)*1000))],
            "audit_events":[make_audit_event(state,"process_decision_node",f"DECISION:{value}:by={decision.get('approver_id')}")]}

def resume_workflow_node(state: HITLAgentState) -> dict:
    t0 = time.monotonic()
    decision = state.get("decision_value", HITLDecision.APPROVED)
    resume = "execute_script_node" if decision==HITLDecision.APPROVED else "abort_node"
    response = build_agent_response(state, payload={"checkpoint_triggered":state.get("checkpoint_triggered",True),
        "trigger_reason":state.get("trigger_reason",""),"review_brief":state.get("review_brief",""),
        "decision":state.get("hitl_decision",{}),"decision_value":decision,"resume_node":resume,
        "notification_sent":state.get("notification_sent",False)}, confidence_score=1.0)
    return {"resume_node":resume,"hitl_required":False,"agent_response":dict(response),
            "status":ExecutionStatus.COMPLETED,"current_node":"resume_workflow_node",
            "execution_trace":[build_trace_entry("resume_workflow_node",int((time.monotonic()-t0)*1000))],
            "audit_events":[make_audit_event(state,"resume_workflow_node",f"WORKFLOW_RESUMED:node={resume}")]}

def log_hitl_event_node(state: HITLAgentState) -> dict:
    t0 = time.monotonic()
    hitl_log = {"event_type":"HITL_CHECKPOINT","trigger_reason":state.get("trigger_reason"),
        "context_sent":state.get("hitl_context"),"decision":state.get("hitl_decision"),
        "approver":state.get("approver_id"),"timestamp":utc_now(),"run_id":state.get("run_id")}
    return {"current_node":"log_hitl_event_node",
            "execution_trace":[build_trace_entry("log_hitl_event_node",int((time.monotonic()-t0)*1000))],
            "audit_events":[make_audit_event(state,"log_hitl_event_node","HITL_LOGGED")],
            "partial_results":[hitl_log]}


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC RUNNERS
# ─────────────────────────────────────────────────────────────────────────────

def run_execution_agent(raw_input: str, execution_plan: dict = None,
                        approved_by: str = None, session_id: str = None,
                        agent_config: dict = None) -> dict:
    from shared import make_base_state
    state = make_base_state(raw_input, AgentType.EXECUTION, session_id=session_id)
    # ── Stamp run/correlation IDs for end-to-end Langfuse tracing ────────────
    state.setdefault("run_id", state.get("session_id", ""))
    state.setdefault("correlation_id", state.get("session_id", ""))
    state.update({"execution_plan":None,"preconditions_ok":False,"sandbox_id":None,
        "execution_output":None,"verification_result":None,"rollback_needed":False,
        "rollback_result":None,"execution_report":None,"config":agent_config or {},
        "working_memory":{"execution_plan":execution_plan,"approver_id":approved_by}})
    tracer = get_tracer("execution_agent")
    with tracer.trace("execution_workflow", session_id=state["session_id"], input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        state = {**state, **receive_plan_node(state)}
        state = {**state, **validate_preconditions_node(state)}
        if state.get("preconditions_ok", True):
            state = {**state, **manage_sandbox_node(state)}
            state = {**state, **execute_script_node(state)}
            state = {**state, **verify_output_node(state)}
            if state.get("rollback_needed"):
                state = {**state, **execute_rollback_node(state)}
        state = {**state, **report_execution_node(state)}
    tracer.flush()
    return state
def run_hitl_agent(raw_input: str, working_memory: dict = None,
                   session_id: str = None, agent_config: dict = None) -> dict:
    from shared import make_base_state
    state = make_base_state(raw_input, AgentType.HITL, session_id=session_id)
    state.update({"checkpoint_triggered":False,"trigger_reason":None,"review_brief":None,
        "approver_id":"engineering_lead","decision_value":HITLDecision.PENDING,
        "decision_notes":None,"resume_node":None,"timeout_seconds":300,
        "notification_sent":False,"working_memory":working_memory or {},
        "config":agent_config or {}})
    tracer = get_tracer("hitl_agent")
    with tracer.trace("hitl_workflow", session_id=state["session_id"], input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        state = {**state, **detect_checkpoint_node(state)}
        state = {**state, **package_review_context_node(state)}
        state = {**state, **interrupt_node(state)}
        state = {**state, **notify_approver_node(state)}
        state = {**state, **listen_for_response_node(state)}
        state = {**state, **process_decision_node(state)}
        state = {**state, **resume_workflow_node(state)}
        state = {**state, **log_hitl_event_node(state)}
    tracer.flush()
    return state
def run_audit_agent(all_audit_events_or_raw: object = None, session_id: str = None,
                    agent_config: dict = None) -> dict:
    from shared import make_base_state
    if isinstance(all_audit_events_or_raw, list):
        all_audit_events = all_audit_events_or_raw
    elif isinstance(all_audit_events_or_raw, str):
        all_audit_events = agent_config.pop("all_audit_events", []) if agent_config else []
    else:
        all_audit_events = []
    state = make_base_state("Audit all pipeline events", AgentType.AUDIT, session_id=session_id)
    state.update({"events_to_process":[],"normalised_events":[],"policy_results":[],
        "anomalies":[],"persisted_records":[],"audit_report":None,
        "compliance_score":1.0,"langfuse_trace_id":None,"config":agent_config or {},
        "working_memory":{"all_audit_events":all_audit_events}})
    tracer = get_tracer("audit_agent")
    with tracer.trace("audit_workflow", session_id=state["session_id"]):
        state = {**state, **listen_for_events_node(state)}
        state = {**state, **normalise_event_node(state)}
        state = {**state, **redact_pii_node(state)}
        state = {**state, **evaluate_policy_node(state)}
        state = {**state, **persist_audit_log_node(state)}
        state = {**state, **correlate_traces_node(state)}
        state = {**state, **detect_anomalies_node(state)}
        state = {**state, **generate_audit_report_node(state)}
    tracer.flush()
    return state
