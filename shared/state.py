"""
shared/state.py
===============
Universal state contracts for all 11 agent accelerators.
Every agent's TypedDict extends BaseAgentState.
"""

from __future__ import annotations

import operator
import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Annotated, Any, Literal, Optional

from typing_extensions import TypedDict


# ─────────────────────────────────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────────────────────────────────

class AgentType(StrEnum):
    # ── Core orchestration agents ─────────────────────────────────────────
    SCHEDULER     = "SCHEDULER_AGENT"   # kept for backward compat (alias for ROUTER)
    ROUTER        = "ROUTER_AGENT"      # Layer 0 — entry-point / dispatcher
    INTENT        = "INTENT_AGENT"      # Layer 1 — intent classification
    PLANNER       = "PLANNER_AGENT"     # Layer 1 — task decomposition
    WORKFLOW      = "WORKFLOW_AGENT"    # Layer 1 — workflow orchestration
    # ── Intelligence agents ───────────────────────────────────────────────
    REASONING     = "REASONING_AGENT"   # Layer 2 — chain-of-thought reasoning
    GENERATOR     = "GENERATOR_AGENT"   # Layer 2 — document / content generation
    COMMUNICATION = "COMMUNICATION_AGENT" # Layer 2 — omnichannel messaging
    TRANSLATION   = "TRANSLATION_AGENT" # Layer 2 — multilingual translation
    # ── Data agents ───────────────────────────────────────────────────────
    SQL           = "SQL_AGENT"         # Layer 2 — natural-language SQL
    PDF_INGESTOR  = "PDF_INGESTOR_AGENT" # Layer 2 — PDF → vector store
    VECTOR_QUERY  = "VECTOR_QUERY_AGENT" # Layer 2 — RAG retrieval
    API_QUERY     = "API_QUERY_AGENT"   # Layer 2 — dynamic API invocation
    # ── Integration agents ────────────────────────────────────────────────
    EMAIL_HANDLER = "EMAIL_HANDLER_AGENT" # Layer 2 — email parse / reply
    MCP_INVOKER   = "MCP_INVOKER_AGENT" # Layer 2 — MCP tool invocation
    SALESFORCE    = "SALESFORCE_AGENT"  # Layer 2 — Salesforce CRM
    SAP           = "SAP_AGENT"         # Layer 2 — SAP RFC / BAPI
    # ── Governance agents ─────────────────────────────────────────────────
    EXECUTION     = "EXECUTION_AGENT"   # Layer 3 — script execution / sandbox
    HITL          = "HITL_AGENT"        # Layer 3 — human-in-the-loop
    AUDIT         = "AUDIT_AGENT"       # Layer 3 — compliance / audit trail
    NOTIFICATION  = "NOTIFICATION_AGENT" # Layer 3 — event-driven notifications
    SCHEDULING    = "SCHEDULING_AGENT"  # Layer 3 — calendar / event scheduling


class AgentIntent(StrEnum):
    ROUTE_INTENT      = "ROUTE_INTENT"
    CREATE_PLAN       = "CREATE_PLAN"
    EXECUTE_WORKFLOW  = "EXECUTE_WORKFLOW"
    REASON            = "REASON"
    GENERATE_CONTENT  = "GENERATE_CONTENT"
    COMMUNICATE       = "COMMUNICATE"
    EXECUTE_SCRIPT    = "EXECUTE_SCRIPT"
    HITL_APPROVAL     = "HITL_APPROVAL"
    AUDIT_LOG         = "AUDIT_LOG"
    GENERAL_CHAT      = "GENERAL_CHAT"
    UNKNOWN           = "UNKNOWN"


class ExecutionStatus(StrEnum):
    PENDING        = "PENDING"
    RUNNING        = "RUNNING"
    PENDING_HUMAN  = "PENDING_HUMAN"
    COMPLETED      = "COMPLETED"
    FAILED         = "FAILED"
    CANCELLED      = "CANCELLED"


class Priority(StrEnum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class HITLDecision(StrEnum):
    APPROVED  = "APPROVED"
    REJECTED  = "REJECTED"
    MODIFIED  = "MODIFIED"
    ESCALATED = "ESCALATED"
    PENDING   = "PENDING"


# ─────────────────────────────────────────────────────────────────────────────
# SUPPORTING SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class AgentMessage(TypedDict):
    """Standard inter-agent communication envelope."""
    message_id:     str
    from_agent:     str
    to_agent:       str
    intent:         str
    payload:        dict
    correlation_id: str
    timestamp:      str
    priority:       str
    ttl_seconds:    int


class ExecutionMetadata(TypedDict):
    """Performance + tracing fields populated by every node."""
    node_name:       str
    started_at:      str
    completed_at:    str
    duration_ms:     int
    llm_tokens_used: int
    llm_model:       str
    retry_count:     int
    error:           Optional[str]


class AuditEvent(TypedDict):
    """Immutable audit record appended by Audit Agent."""
    event_id:       str
    timestamp:      str
    agent_type:     str
    node_name:      str
    correlation_id: str
    user_id:        Optional[str]
    action:         str
    inputs_hash:    str
    outputs_hash:   str
    policy_ok:      bool
    violations:     list


class ConfidenceScore(TypedDict):
    score:  float          # 0.0 – 1.0
    level:  str            # "low" | "medium" | "high"
    flags:  list[str]


class AgentResponse(TypedDict):
    """Universal output envelope — all agents return this."""
    response_id:    str
    correlation_id: str
    run_id:         str
    agent_type:     str
    status:         str
    timestamp:      str
    payload:        dict
    confidence:     ConfidenceScore
    sources:        list[dict]
    hitl_request:   Optional[dict]
    execution:      dict
    error:          Optional[dict]
    routing_hints:  dict


# ─────────────────────────────────────────────────────────────────────────────
# BASE STATE — inherited by ALL agents
# ─────────────────────────────────────────────────────────────────────────────

class BaseAgentState(TypedDict):
    # ── Identity & Routing ──────────────────────────────────────────────────
    session_id:      str
    correlation_id:  str
    run_id:          str
    agent_type:      str
    user_id:         Optional[str]
    tenant_id:       Optional[str]

    # ── Input ────────────────────────────────────────────────────────────────
    raw_input:          str
    normalised_input:   Optional[str]
    input_channel:      Optional[str]   # "chat" | "api" | "email"
    input_language:     Optional[str]   # BCP-47 e.g. "en"

    # ── Execution Control ────────────────────────────────────────────────────
    status:          str                # ExecutionStatus value
    current_node:    str
    next_node:       Optional[str]
    retry_count:     Annotated[int, lambda a, b: b]
    max_retries:     int
    error_history:   Annotated[list, operator.add]

    # ── Memory ───────────────────────────────────────────────────────────────
    conversation_history: Annotated[list, operator.add]
    working_memory:       dict
    long_term_memory_keys: list

    # ── Inter-Agent Communication ────────────────────────────────────────────
    inbound_messages:  Annotated[list, operator.add]
    outbound_messages: Annotated[list, operator.add]

    # ── Output ───────────────────────────────────────────────────────────────
    agent_response:  Optional[dict]
    partial_results: Annotated[list, operator.add]

    # ── Governance ───────────────────────────────────────────────────────────
    audit_events:    Annotated[list, operator.add]
    execution_trace: Annotated[list, operator.add]
    hitl_required:   bool
    hitl_context:    Optional[dict]
    hitl_decision:   Optional[dict]

    # ── Config & Feature Flags ───────────────────────────────────────────────
    config:          dict
    feature_flags:   dict


# ─────────────────────────────────────────────────────────────────────────────
# AGENT-SPECIFIC STATE EXTENSIONS
# ─────────────────────────────────────────────────────────────────────────────

class SchedulerAgentState(BaseAgentState):
    required_agents:     list[str]
    parallel_safe:       bool
    priority:            str
    load_metrics:        dict
    routing_plan:        Optional[dict]
    activated_agents:    list[str]
    agent_results:       Annotated[list, operator.add]
    final_response:      Optional[str]


class RouterAgentState(BaseAgentState):
    required_agents:     list[str]
    parallel_safe:       bool
    priority:            str
    load_metrics:        dict
    routing_plan:        Optional[dict]
    activated_agents:    list[str]
    agent_results:       Annotated[list, operator.add]
    final_response:      Optional[str]

class IntentAgentState(BaseAgentState):
    detected_intents:    list[dict]
    primary_intent:      Optional[str]
    extracted_entities:  dict
    sub_tasks:           list[dict]
    routing_decision:    Optional[str]
    clarification_needed: bool
    clarification_q:     Optional[str]
    aggregated_results:  Optional[dict]
    confidence_threshold: float


class PlannerAgentState(BaseAgentState):
    goal_analysis:       Optional[dict]
    task_graph:          list[dict]
    execution_order:     list[str]
    agent_assignments:   dict
    resource_estimates:  dict
    validated_plan:      Optional[dict]
    workflow_plan:       Optional[dict]
    plan_id:             Optional[str]


class WorkflowAgentState(BaseAgentState):
    workflow_definition: Optional[dict]
    current_step_index:  int
    current_step:        Optional[dict]
    completed_steps:     Annotated[list, operator.add]
    step_results:        dict
    workflow_status:     str
    condition_results:   dict
    workflow_summary:    Optional[str]


class ReasoningAgentState(BaseAgentState):
    framed_problem:      Optional[dict]
    hypotheses:          list[dict]
    evidence_set:        list[dict]
    reasoning_chain:     list[dict]
    conclusion:          Optional[dict]
    reasoning_valid:     bool
    reasoning_issues:    list[str]
    tool_results:        Annotated[list, operator.add]


class GeneratorAgentState(BaseAgentState):
    template_id:         Optional[str]
    collected_inputs:    dict
    content_outline:     Optional[dict]
    generated_sections:  Annotated[list, operator.add]
    review_result:       Optional[dict]
    refined_content:     Optional[str]
    final_document:      Optional[str]
    generation_config:   dict


class CommunicationAgentState(BaseAgentState):
    detected_channel:    Optional[str]
    message_type:        Optional[str]
    message_urgency:     Optional[str]
    draft_response:      Optional[str]
    consistency_ok:      bool
    dispatch_result:     Optional[dict]
    tone:                str
    channel_config:      dict


class ExecutionAgentState(BaseAgentState):
    execution_plan:      Optional[dict]
    preconditions_ok:    bool
    sandbox_id:          Optional[str]
    execution_output:    Optional[dict]
    verification_result: Optional[dict]
    rollback_needed:     bool
    rollback_result:     Optional[dict]
    execution_report:    Optional[str]


class HITLAgentState(BaseAgentState):
    checkpoint_triggered: bool
    trigger_reason:       Optional[str]
    review_brief:         Optional[str]
    approver_id:          Optional[str]
    decision_value:       str
    decision_notes:       Optional[str]
    resume_node:          Optional[str]
    timeout_seconds:      int
    notification_sent:    bool


class AuditAgentState(BaseAgentState):
    events_to_process:   list[dict]
    normalised_events:   Annotated[list, operator.add]
    policy_results:      Annotated[list, operator.add]
    anomalies:           Annotated[list, operator.add]
    persisted_records:   Annotated[list, operator.add]
    audit_report:        Optional[dict]
    compliance_score:    float
    langfuse_trace_id:   Optional[str]


# ─────────────────────────────────────────────────────────────────────────────
# FACTORY HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def make_base_state(
    raw_input: str,
    agent_type: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    config: Optional[dict] = None,
    feature_flags: Optional[dict] = None,
) -> dict:
    """Build a minimal valid BaseAgentState dict."""
    return {
        "session_id":      session_id or new_id("sess"),
        "correlation_id":  new_id("corr"),
        "run_id":          new_id("run"),
        "agent_type":      agent_type,
        "user_id":         user_id,
        "tenant_id":       None,
        "raw_input":       raw_input,
        "normalised_input": None,
        "input_channel":   "chat",
        "input_language":  "en",
        "status":          ExecutionStatus.PENDING,
        "current_node":    "start",
        "next_node":       None,
        "retry_count":     0,
        "max_retries":     3,
        "error_history":   [],
        "conversation_history": [],
        "working_memory":  {},
        "long_term_memory_keys": [],
        "inbound_messages":  [],
        "outbound_messages": [],
        "agent_response":  None,
        "partial_results": [],
        "audit_events":    [],
        "execution_trace": [],
        "hitl_required":   False,
        "hitl_context":    None,
        "hitl_decision":   None,
        "config":          config or {},
        "feature_flags":   feature_flags or {
            "pii_redaction": True,
            "audit":         True,
            "hitl_enabled":  True,
        },
    }


def build_agent_response(
    state: dict,
    payload: dict,
    confidence_score: float = 0.9,
    sources: Optional[list] = None,
    error: Optional[dict] = None,
) -> AgentResponse:
    """Build a standard AgentResponse from any agent's final state."""
    # Coerce to float — real LLM responses may return numeric fields as strings
    try:
        confidence_score = float(confidence_score)
    except (TypeError, ValueError):
        confidence_score = 0.9
    # Clamp to [0.0, 1.0]
    confidence_score = max(0.0, min(1.0, confidence_score))
    level = "high" if confidence_score >= 0.8 else ("medium" if confidence_score >= 0.5 else "low")
    trace = state.get("execution_trace", [])
    total_ms = sum(t.get("duration_ms", 0) for t in trace)
    total_tokens = sum(t.get("llm_tokens_used", 0) for t in trace)
    llm_calls = sum(1 for t in trace if t.get("llm_tokens_used", 0) > 0)

    return AgentResponse(
        response_id=new_id("resp"),
        correlation_id=state.get("correlation_id", ""),
        run_id=state.get("run_id", ""),
        agent_type=state.get("agent_type", ""),
        status=state.get("status", ExecutionStatus.COMPLETED),
        timestamp=utc_now(),
        payload=payload,
        confidence=ConfidenceScore(
            score=confidence_score,
            level=level,
            flags=[],
        ),
        sources=sources or [],
        hitl_request=state.get("hitl_context"),
        execution={
            "total_duration_ms": total_ms,
            "llm_calls":         llm_calls,
            "total_tokens":      total_tokens,
            "nodes_executed":    [t.get("node_name") for t in trace],
            "retries":           state.get("retry_count", 0),
        },
        error=error,
        routing_hints={
            "suggested_next_agents": [],
            "can_run_parallel":      False,
        },
    )


def make_audit_event(
    state: dict,
    node_name: str,
    action: str,
    policy_ok: bool = True,
    violations: Optional[list] = None,
) -> AuditEvent:
    return AuditEvent(
        event_id=new_id("evt"),
        timestamp=utc_now(),
        agent_type=state.get("agent_type", ""),
        node_name=node_name,
        correlation_id=state.get("correlation_id", ""),
        user_id=state.get("user_id"),
        action=action,
        inputs_hash=uuid.uuid4().hex[:8],
        outputs_hash=uuid.uuid4().hex[:8],
        policy_ok=policy_ok,
        violations=violations or [],
    )


def make_message(
    from_agent: str,
    to_agent: str,
    intent: str,
    payload: dict,
    correlation_id: str,
    priority: str = Priority.MEDIUM,
) -> AgentMessage:
    return AgentMessage(
        message_id=new_id("msg"),
        from_agent=from_agent,
        to_agent=to_agent,
        intent=intent,
        payload=payload,
        correlation_id=correlation_id,
        timestamp=utc_now(),
        priority=priority,
        ttl_seconds=300,
    )
