from __future__ import annotations
"""agents/scheduling/graph.py — Scheduling Agent."""
from shared import (
    BaseAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

from shared.langfuse_manager import get_tracer
from agents.scheduling.nodes.scheduling_agent_nodes import (
    parse_schedule_intent_node,check_availability_node,create_event_invitation_node,
    dispatch_calendar_event_node,confirm_scheduling_node)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/scheduling/nodes/ location is preserved for backward compatibility.
from agents.scheduling.workflows.nodes import (
    parse_schedule_intent_node, check_availability_node, create_event_invitation_node, dispatch_calendar_event_node, confirm_scheduling_node,
)


def run_scheduling_agent(raw_input:str,session_id:str=None,agent_config:dict=None)->dict:
    """NL scheduling: parse intent → availability check → event creation → dispatch → confirm.
    Consumer config: calendar.platform (outlook|teams|google), calendar.credentials,
    prompts.parse_intent / check_availability / create_event / confirm.
    """
    state=make_base_state(raw_input,AgentType.SCHEDULING,session_id=session_id)
    state.update({"sched_action":None,"event_type":None,"sched_participants":[],"preferred_time":"",
        "duration_minutes":60,"platform":"Teams","recurrence":None,"calendar_available":True,
        "scheduling_conflicts":[],"suggested_alternatives":[],"event_invitation":{},
        "event_subject":None,"event_body":None,"calendar_result":{},"scheduling_summary":None,"config":agent_config or {}})
    tracer=get_tracer("scheduling")
    with tracer.trace("scheduling_workflow",session_id=state["session_id"],input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        for fn in [parse_schedule_intent_node,check_availability_node,
                   create_event_invitation_node,dispatch_calendar_event_node,confirm_scheduling_node]:
            state={**state,**fn(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("scheduling_summary")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_scheduling_agent", "AGENT_COMPLETED")
    )
    return state
