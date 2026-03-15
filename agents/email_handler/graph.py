from __future__ import annotations
"""agents/email_handler/graph.py — Email Handler Agent entry point."""
from shared import (
    BaseAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

from shared.langfuse_manager import get_tracer
from agents.email_handler.nodes.email_handler_nodes import (
    fetch_email_node, process_attachments_node, parse_email_node,
    classify_email_node, route_action_node, draft_reply_node, dispatch_email_node,
)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/email_handler/nodes/ location is preserved for backward compatibility.
from agents.email_handler.workflows.nodes import (
    fetch_email_node, process_attachments_node, parse_email_node, classify_email_node, route_action_node, draft_reply_node, dispatch_email_node,
)



def run_email_handler_agent(
    raw_input: str,
    session_id: str = None,
    agent_config: dict = None,
) -> dict:
    """Process an inbound email end-to-end: fetch → parse → classify → route → reply → dispatch.

    Consumer config keys (agent_config):
        mailbox.protocol: mock | imap | graph_api | gmail_api
        mailbox.host / mailbox.credentials (for real connectors)
        reply_tone: professional | friendly | formal
        org_name: str
        batch_size: int
        quality_threshold: float
        prompts.parse / prompts.classify / prompts.draft_reply / prompts.route
    """
    state = make_base_state(raw_input, AgentType.EMAIL_HANDLER, session_id=session_id)
    state.update({
        "email_id": None, "raw_email": None, "email_subject": "",
        "email_sender": "", "email_body": "", "email_attachments": [],
        "parsed_email": {}, "email_intent": None, "email_entities": {},
        "email_category": None, "email_classification": {}, "requires_human": False,
        "classification_confidence": 0.0, "action_route": None,
        "reply_draft": None, "delivery_receipt": None, "reply_sent": False,
        "config": agent_config or {},
    })
    tracer = get_tracer("email_handler_agent")
    with tracer.trace("email_handler_workflow", session_id=state["session_id"], input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        state = {**state, **fetch_email_node(state)}
        state = {**state, **process_attachments_node(state)}
        state = {**state, **parse_email_node(state)}
        state = {**state, **classify_email_node(state)}
        state = {**state, **route_action_node(state)}
        if not state.get("requires_human"):
            state = {**state, **draft_reply_node(state)}
            state = {**state, **dispatch_email_node(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("reply_draft")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_email_handler_agent", "AGENT_COMPLETED")
    )
    return state
