from __future__ import annotations
"""agents/notification/graph.py — Notification Agent."""
from shared import (
    BaseAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

from shared.langfuse_manager import get_tracer
from agents.notification.nodes.notification_agent_nodes import (
    receive_event_node,enrich_event_context_node,resolve_recipients_node,classify_priority_node,
    select_channel_node,craft_message_node,deduplicate_notification_node,dispatch_notification_node,track_engagement_node)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/notification/nodes/ location is preserved for backward compatibility.
from agents.notification.workflows.nodes import (
    receive_event_node, enrich_event_context_node, resolve_recipients_node, classify_priority_node, select_channel_node, craft_message_node, deduplicate_notification_node, dispatch_notification_node, track_engagement_node,
)


def run_notification_agent(raw_input:str,event_payload:dict=None,session_id:str=None,agent_config:dict=None)->dict:
    """Event-driven notification: receive → enrich → resolve recipients → craft → dedup → dispatch → track.
    Consumer config: channels.email/sms/teams/slack, user_preferences, notification_rules,
    dedup_window_minutes, org_context, prompts.*.
    """
    state=make_base_state(raw_input,AgentType.NOTIFICATION,session_id=session_id)
    state.update({"event_payload":event_payload,"normalised_event":{},"enriched_event":{},"event_type":None,
        "recipients":[],"escalation_chain":[],"notification_priority":"medium","send_immediately":True,
        "batch_eligible":False,"selected_channel":None,"fallback_channel":None,"crafted_message":None,
        "is_duplicate":False,"dispatch_result":{},"engagement_tracking":{},"config":agent_config or {}})
    tracer=get_tracer("notification")
    with tracer.trace("notification_workflow",session_id=state["session_id"],input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        for fn in [receive_event_node,enrich_event_context_node,resolve_recipients_node,classify_priority_node,
                   select_channel_node,craft_message_node,deduplicate_notification_node,
                   dispatch_notification_node,track_engagement_node]:
            state={**state,**fn(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("dispatch_result")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_notification_agent", "AGENT_COMPLETED")
    )
    return state
