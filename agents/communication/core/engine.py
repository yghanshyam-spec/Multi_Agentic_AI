"""
agents/communication/core/engine.py
=====================================
Communication Agent engine — entry point called by the pipeline.

Tracing: shared.langfuse_manager only (no local LangfuseClient or PromptManager).
Prompts: shared.langfuse_manager.get_prompt() only.
"""
from __future__ import annotations

import os
import sys
import types
import uuid
import time
from typing import Any, Dict, List, Optional

from shared.common import (
    get_llm, call_llm, get_tracer, get_logger,
    AgentType, ExecutionStatus,
    make_base_state, build_agent_response, make_audit_event,
    build_trace_entry, new_id, utc_now,
)
from shared.langfuse_manager import get_prompt as _lf_get_prompt
from shared import (
    BaseAgentState, AgentMessage, ExecutionMetadata,
    CommunicationAgentState,
)

logger = get_logger(__name__)

# ── Step 1: register the communication sub-package so that internal imports
#            like ``from communication.schemas.graph_state import ...`` work.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))          # .../communication/core
_COMM_DIR = os.path.dirname(_THIS_DIR)                           # .../communication

if _COMM_DIR not in sys.path:
    sys.path.insert(0, _COMM_DIR)

if "communication" not in sys.modules:
    _pkg = types.ModuleType("communication")
    _pkg.__path__ = [_COMM_DIR]
    _pkg.__package__ = "communication"
    _pkg.__spec__ = None
    sys.modules["communication"] = _pkg

# ── Step 2: LangGraph ────────────────────────────────────────────────────────
try:
    from langgraph.graph import StateGraph, END
    _LG_AVAILABLE = True
except ImportError:
    _LG_AVAILABLE = False

# ── Step 3: Import the real sub-package components ───────────────────────────
try:
    from communication.schemas.graph_state import (
        OmnichannelState, BroadcastState, GenericCommState,
    )
    from communication.tools.communication_tools import (
        ContextMemoryTool, ChannelDispatcher, CRMLogTool, AuditLogTool,
    )
    from communication.sub_agents.specialist_agent import CommunicationSpecialistAgent
    from communication.workflows.create_graph import GraphFactory
    from communication.workflows.nodes.omnichannel_nodes import make_omnichannel_nodes
    from communication.workflows.nodes.broadcast_nodes import make_broadcast_nodes
    from communication.workflows.edges import build_conditional_router
    from communication.utils.helpers import now_iso, word_count, sentiment_hint
    from communication.utils.logger import get_logger as _comm_get_logger
    _COMM_SUBPKG = True
except (ImportError, Exception) as _e:
    _COMM_SUBPKG = False
    import logging as _logging
    def _comm_get_logger(name): return _logging.getLogger(name)
    now_iso = utc_now
    def word_count(t): return len(t.split())
    def sentiment_hint(t): return "neutral"

logger = _comm_get_logger(__name__)


# ── Shared tool instances ─────────────────────────────────────────────────────
if _COMM_SUBPKG:
    _TOOLS = {
        "memory":     ContextMemoryTool(),
        "dispatcher": ChannelDispatcher({"mock_mode": "true"}),
        "crm":        CRMLogTool(),
        "audit":      AuditLogTool(),
    }
else:
    _TOOLS = {"memory": None, "dispatcher": None, "crm": None, "audit": None}

_NODE_CONFIG = {
    "omnichannel": {
        "max_history_entries": 20,
        "escalation_keywords": [
            "urgent", "lawyer", "legal", "sue", "refund",
            "unacceptable", "escalate", "complaint", "ombudsman",
        ],
        "escalation_channel": "email",
        "reply_channel_preference": {
            "email": "email", "chat": "chat",
            "slack": "slack", "voice": "email", "api": "api",
        },
    },
    "broadcast": {
        "max_history_entries": 10,
        "default_channels": ["email", "slack", "memo"],
        "auto_fix_contradictions": True,
    },
    "channel_rules": {
        "email":   {"tone": "professional",         "max_words": 300},
        "chat":    {"tone": "friendly_casual",      "max_words": 80},
        "slack":   {"tone": "conversational",       "max_words": 120},
        "teams":   {"tone": "professional",         "max_words": 200},
        "api":     {"tone": "technical_concise",    "max_words": 150},
        "memo":    {"tone": "formal_authoritative", "max_words": 600},
        "default": {"tone": "professional",         "max_words": 200},
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# ENGINE CLASS
# ─────────────────────────────────────────────────────────────────────────────

class CommunicationAgentEngine:
    """
    Central engine for the Communication Agent accelerator.

    Usage::

        engine = CommunicationAgentEngine()
        result = engine.run_agent(
            raw_input="Customer complaint about invoice",
            channel="email",
        )
    """

    def __init__(self, agent_config: dict | None = None):
        self._config  = agent_config or {}
        self._llm     = get_llm()
        self._tracer  = get_tracer("communication_agent")
        self._graph   = None
        logger.info("[CommunicationAgentEngine] initialised")

    def run_agent(
        self,
        raw_input: str,
        channel: str = "email",
        working_memory: dict = None,
        session_id: str = None,
        inbound_payload: dict = None,
        target_channels: list = None,
        talking_points: str = None,
    ) -> dict:
        """Delegate to the public runner, injecting the pre-compiled graph."""
        if self._graph is None:
            self._graph = build_communication_graph()
        return run_communication_agent(
            raw_input=raw_input,
            channel=channel,
            working_memory=working_memory,
            session_id=session_id,
            inbound_payload=inbound_payload,
            target_channels=target_channels,
            talking_points=talking_points,
            agent_config=self._config,
            graph=self._graph,
        )


# ─────────────────────────────────────────────────────────────────────────────
# LLM BRIDGE — makes accelerator LLM look like a LangChain model
# ─────────────────────────────────────────────────────────────────────────────

class _AcceleratorLLMBridge:
    def invoke(self, prompt: str):
        llm    = get_llm()
        result = call_llm(llm, prompt, prompt[:200], node_hint="comm_agent")
        raw    = result.get("raw_response", str(result))

        class _Resp:
            def __init__(self, text): self.content = text
        return _Resp(raw)


def _make_specialist_agent():
    """Instantiate specialist agent — tracing via shared.langfuse_manager."""
    if not _COMM_SUBPKG:
        return None
    return CommunicationSpecialistAgent(
        llm=_AcceleratorLLMBridge(),
        agent_config={},
    )


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def _build_omnichannel_langgraph():
    agent    = _make_specialist_agent()
    node_fns = make_omnichannel_nodes(agent, _TOOLS, _NODE_CONFIG)

    graph = StateGraph(OmnichannelState)
    for node_id, fn in node_fns.items():
        graph.add_node(node_id, fn)

    graph.set_entry_point("detect_channel_node")
    graph.add_edge("detect_channel_node",    "load_context_node")
    graph.add_edge("load_context_node",      "classify_message_node")
    graph.add_edge("classify_message_node",  "draft_response_node")
    graph.add_edge("draft_response_node",    "check_consistency_node")
    graph.add_edge("check_consistency_node", "dispatch_response_node")
    graph.add_edge("dispatch_response_node", "update_context_node")
    graph.add_edge("update_context_node",    END)

    logger.info("Omnichannel LangGraph compiled (7 nodes)")
    return graph.compile()


def _build_broadcast_langgraph():
    agent    = _make_specialist_agent()
    node_fns = make_broadcast_nodes(agent, _TOOLS, _NODE_CONFIG)

    graph = StateGraph(BroadcastState)
    for node_id, fn in node_fns.items():
        graph.add_node(node_id, fn)

    graph.set_entry_point("detect_channel_node")
    graph.add_edge("detect_channel_node",    "load_context_node")
    graph.add_edge("load_context_node",      "classify_message_node")
    graph.add_edge("classify_message_node",  "draft_response_node")
    graph.add_edge("draft_response_node",    "check_consistency_node")
    graph.add_edge("check_consistency_node", "dispatch_response_node")
    graph.add_edge("dispatch_response_node", "update_context_node")
    graph.add_edge("update_context_node",    END)

    logger.info("Broadcast LangGraph compiled (7 nodes)")
    return graph.compile()


# ─────────────────────────────────────────────────────────────────────────────
# STATE TRANSLATORS
# ─────────────────────────────────────────────────────────────────────────────

def _accel_to_omnichannel(state: dict) -> dict:
    wm = state.get("working_memory", {})
    return {
        "user_message":         state.get("raw_input", ""),
        "inbound_payload":      wm.get("inbound_payload", {
            "channel": state.get("detected_channel", "email"),
            "body":    state.get("raw_input", ""),
            "sender":  "pipeline@company.com",
            "subject": "Incident Response Notification",
        }),
        "session_id":           state.get("session_id", str(uuid.uuid4())),
        "trace_id":             new_id("trace"),
        "workflow":             "omnichannel_response",
        "metadata":             wm.get("metadata", {}),
        "normalised_message":   None,
        "detected_channel":     None,
        "conversation_history": [],
        "context_summary":      None,
        "classification":       None,
        "draft_response":       None,
        "preferred_reply_channel": None,
        "channel_rules":        None,
        "consistency_report":   None,
        "dispatch_results":     [],
        "crm_logged":           False,
        "audit_entry":          None,
        "current_node":         None,
        "error":                None,
    }


def _accel_to_broadcast(state: dict) -> dict:
    wm = state.get("working_memory", {})
    return {
        "user_message":         state.get("raw_input", ""),
        "talking_points":       wm.get("talking_points", state.get("raw_input", "")),
        "target_channels":      wm.get("target_channels", ["email", "slack", "memo"]),
        "inbound_payload":      {},
        "session_id":           state.get("session_id", str(uuid.uuid4())),
        "trace_id":             new_id("trace"),
        "workflow":             "broadcast_drafting",
        "metadata":             wm.get("metadata", {}),
        "normalised_message":   None,
        "detected_channel":     None,
        "conversation_history": [],
        "context_summary":      None,
        "classification":       None,
        "channel_drafts":       [],
        "draft_response":       None,
        "consistency_report":   None,
        "consistency_fixed":    False,
        "dispatch_results":     [],
        "audit_entry":          None,
        "current_node":         None,
        "error":                None,
    }


def _omnichannel_to_accel_delta(sub_result: dict, orig: dict) -> dict:
    cls      = sub_result.get("classification") or {}
    dispatch = sub_result.get("dispatch_results") or [{}]
    audit    = sub_result.get("audit_entry") or {}
    report   = sub_result.get("consistency_report") or {}
    return {
        "detected_channel": sub_result.get("detected_channel",
                             orig.get("detected_channel", "email")),
        "message_type":    cls.get("classification", "automated_response"),
        "message_urgency": cls.get("priority", "medium"),
        "draft_response":  sub_result.get("draft_response", ""),
        "consistency_ok":  report.get("is_consistent", True),
        "dispatch_result": dispatch[0] if dispatch else {},
        "working_memory":  {
            **orig.get("working_memory", {}),
            "classification":     cls,
            "dispatch_results":   dispatch,
            "crm_logged":         sub_result.get("crm_logged", False),
            "audit_id":           audit.get("audit_id"),
            "normalised_message": sub_result.get("normalised_message", {}),
            "reply_channel":      sub_result.get("preferred_reply_channel"),
        },
    }


def _broadcast_to_accel_delta(sub_result: dict, orig: dict) -> dict:
    drafts   = sub_result.get("channel_drafts") or []
    report   = sub_result.get("consistency_report") or {}
    dispatch = sub_result.get("dispatch_results") or [{}]
    audit    = sub_result.get("audit_entry") or {}
    combined = "\n\n".join(
        f"=== {d['channel'].upper()} ===\n{d['content']}" for d in drafts
    )
    return {
        "detected_channel": "api",
        "message_type":    "broadcast",
        "message_urgency": "medium",
        "draft_response":  combined,
        "consistency_ok":  report.get("is_consistent", True),
        "dispatch_result": dispatch[0] if dispatch else {},
        "working_memory":  {
            **orig.get("working_memory", {}),
            "channel_drafts":     drafts,
            "consistency_report": report,
            "dispatch_results":   dispatch,
            "audit_id":           audit.get("audit_id"),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# ACCELERATOR-LEVEL NODE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def detect_channel_node(state: dict) -> dict:
    t0        = time.monotonic()
    wm        = state.get("working_memory", {})
    payload   = wm.get("inbound_payload", {})
    channel   = (payload.get("channel") or wm.get("input_channel")
                 or state.get("detected_channel", "email"))
    rules_map = _NODE_CONFIG["channel_rules"]
    config    = rules_map.get(channel, rules_map["default"])
    return {
        "detected_channel": channel,
        "channel_config":   config,
        "tone":             config["tone"],
        "status":           ExecutionStatus.RUNNING,
        "current_node":     "detect_channel_node",
        "execution_trace":  [build_trace_entry("detect_channel_node",
                             int((time.monotonic() - t0) * 1000))],
    }


def load_context_node(state: dict) -> dict:
    t0        = time.monotonic()
    thread_id = state.get("session_id", "")
    memory    = _TOOLS["memory"]
    history   = memory.load(thread_id, max_entries=20) if memory else []
    summary   = (memory.get_summary(thread_id) if memory and history
                 else "No prior conversation.")
    return {
        "conversation_history": history,
        "working_memory": {**state.get("working_memory", {}),
                           "context_summary": summary},
        "current_node":    "load_context_node",
        "execution_trace": [build_trace_entry("load_context_node",
                            int((time.monotonic() - t0) * 1000))],
    }


def classify_message_node(state: dict) -> dict:
    t0 = time.monotonic()
    return {
        "message_type":    "pending",
        "message_urgency": "medium",
        "current_node":    "classify_message_node",
        "execution_trace": [build_trace_entry("classify_message_node",
                            int((time.monotonic() - t0) * 1000))],
    }


def draft_response_node(state: dict) -> dict:
    t0 = time.monotonic()
    wm = state.get("working_memory", {})

    if wm.get("target_channels"):
        logger.info("Communication: invoking broadcast sub-graph (UC2)")
        sub_state  = _accel_to_broadcast(state)
        sub_graph  = _build_broadcast_langgraph()
        sub_result = sub_graph.invoke(sub_state)
        delta      = _broadcast_to_accel_delta(sub_result, state)
    else:
        logger.info("Communication: invoking omnichannel sub-graph (UC1)")
        sub_state  = _accel_to_omnichannel(state)
        sub_graph  = _build_omnichannel_langgraph()
        sub_result = sub_graph.invoke(sub_state)
        delta      = _omnichannel_to_accel_delta(sub_result, state)

    return {
        **delta,
        "current_node":    "draft_response_node",
        "execution_trace": [build_trace_entry("draft_response_node",
                            int((time.monotonic() - t0) * 1000), 300)],
        "audit_events":    [make_audit_event(state, "draft_response_node",
                            "RESPONSE_DRAFTED")],
    }


def check_consistency_node(state: dict) -> dict:
    t0 = time.monotonic()
    return {
        "consistency_ok":  state.get("consistency_ok", True),
        "current_node":    "check_consistency_node",
        "execution_trace": [build_trace_entry("check_consistency_node",
                            int((time.monotonic() - t0) * 1000))],
    }


def dispatch_response_node(state: dict) -> dict:
    t0 = time.monotonic()
    dr = state.get("dispatch_result") or {}
    if not dr and _TOOLS.get("dispatcher"):
        dr = _TOOLS["dispatcher"].dispatch(
            state.get("detected_channel", "email"),
            state.get("draft_response", ""),
            {"session_id": state.get("session_id")},
            thread_id=state.get("session_id", ""),
        )
    return {
        "dispatch_result": dr,
        "current_node":    "dispatch_response_node",
        "execution_trace": [build_trace_entry("dispatch_response_node",
                            int((time.monotonic() - t0) * 1000))],
    }


def update_context_node(state: dict) -> dict:
    t0  = time.monotonic()
    wm  = state.get("working_memory", {})
    cls = wm.get("classification", {})
    dr  = state.get("dispatch_result", {})

    response = build_agent_response(
        state,
        payload={
            "channel":         state.get("detected_channel"),
            "reply_channel":   wm.get("reply_channel", state.get("detected_channel")),
            "message_type":    state.get("message_type"),
            "urgency":         state.get("message_urgency"),
            "sentiment":       cls.get("sentiment"),
            "requires_human":  cls.get("requires_human", False),
            "draft_response":  state.get("draft_response", ""),
            "channel_drafts":  wm.get("channel_drafts"),
            "dispatch_result": dr,
            "dispatched":      dr.get("status", "DELIVERED"),
            "consistency_ok":  state.get("consistency_ok", True),
            "crm_logged":      wm.get("crm_logged", False),
        },
        confidence_score=0.92,
    )
    return {
        "agent_response":  dict(response),
        "status":          ExecutionStatus.COMPLETED,
        "current_node":    "update_context_node",
        "execution_trace": [build_trace_entry("update_context_node",
                            int((time.monotonic() - t0) * 1000))],
        "audit_events":    [make_audit_event(state, "update_context_node",
                            "COMM_COMPLETE")],
    }


# ─────────────────────────────────────────────────────────────────────────────
# TOP-LEVEL ACCELERATOR LANGGRAPH
# ─────────────────────────────────────────────────────────────────────────────

def build_communication_graph():
    """
    Compile the top-level CommunicationAgentState LangGraph.
    draft_response_node internally runs the UC1 or UC2 sub-graph.
    Returns None if LangGraph is not installed.
    """
    if not _LG_AVAILABLE:
        logger.warning("[build_communication_graph] langgraph not installed.")
        return None

    graph = StateGraph(CommunicationAgentState)
    graph.add_node("detect_channel_node",    detect_channel_node)
    graph.add_node("load_context_node",      load_context_node)
    graph.add_node("classify_message_node",  classify_message_node)
    graph.add_node("draft_response_node",    draft_response_node)
    graph.add_node("check_consistency_node", check_consistency_node)
    graph.add_node("dispatch_response_node", dispatch_response_node)
    graph.add_node("update_context_node",    update_context_node)

    graph.set_entry_point("detect_channel_node")
    graph.add_edge("detect_channel_node",    "load_context_node")
    graph.add_edge("load_context_node",      "classify_message_node")
    graph.add_edge("classify_message_node",  "draft_response_node")
    graph.add_edge("draft_response_node",    "check_consistency_node")
    graph.add_edge("check_consistency_node", "dispatch_response_node")
    graph.add_edge("dispatch_response_node", "update_context_node")
    graph.add_edge("update_context_node",    END)

    return graph.compile()


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC RUNNER  — called by orchestration/pipeline.py
# ─────────────────────────────────────────────────────────────────────────────

def run_communication_agent(
    raw_input: str,
    channel: str = "email",
    working_memory: dict = None,
    session_id: str = None,
    inbound_payload: dict = None,
    target_channels: list = None,
    talking_points: str = None,
    agent_config: dict = None,
    graph=None,                   # pre-compiled graph from build_communication_graph()
) -> dict:
    """
    Run the Communication Agent end-to-end.

    Parameters
    ----------
    graph : pre-compiled LangGraph (built once by the pipeline and reused).
            If None, a fresh graph is compiled on-the-fly.

    Returns
    -------
    dict — final CommunicationAgentState with agent_response (AgentResponse) set.
    """
    state = make_base_state(raw_input, AgentType.COMMUNICATION, session_id=session_id)
    state.setdefault("run_id",         state.get("session_id", ""))
    state.setdefault("correlation_id", state.get("session_id", ""))

    wm = dict(working_memory or {})
    if inbound_payload:  wm["inbound_payload"]  = inbound_payload
    if target_channels:  wm["target_channels"]  = target_channels
    if talking_points:   wm["talking_points"]   = talking_points

    state.update({
        "detected_channel":     channel,
        "message_type":         None,
        "message_urgency":      None,
        "draft_response":       None,
        "consistency_ok":       True,
        "dispatch_result":      None,
        "tone":                 "professional",
        "channel_config":       {},
        "input_channel":        channel,
        "conversation_history": [],
        "working_memory":       wm,
        "config":               agent_config or {},
    })

    tracer = get_tracer("communication_agent")
    with tracer.trace(
        "communication_workflow",
        session_id=state["session_id"],
        input=raw_input[:200],
        metadata={
            "run_id":         state.get("run_id", ""),
            "correlation_id": state.get("correlation_id", ""),
        },
    ):
        if _COMM_SUBPKG and _LG_AVAILABLE:
            compiled = graph or build_communication_graph()
            if compiled:
                state = dict(compiled.invoke(state))
            else:
                state = _run_fallback(state, raw_input, channel)
        else:
            state = _run_fallback(state, raw_input, channel)

    tracer.flush()

    # Ensure agent_response is always set
    if not state.get("agent_response"):
        state["agent_response"] = dict(build_agent_response(
            state,
            payload={"draft_response": state.get("draft_response"),
                     "channel":         state.get("detected_channel", channel)},
            confidence_score=0.90,
        ))

    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_communication_agent", "AGENT_COMPLETED")
    )
    return state


def _run_fallback(state: dict, raw_input: str, channel: str) -> dict:
    """LLM-only fallback when sub-package deps or LangGraph are unavailable."""
    _SYS = "You are a communication specialist. Draft a response. Return JSON: {draft: str}"
    t0   = time.monotonic()
    res  = call_llm(get_llm(), _SYS, "Draft for: " + raw_input, node_hint="draft_response")
    draft = res.get("draft", res.get("raw_response",
            "Re: " + raw_input + " — Thank you for your message."))
    state["draft_response"]  = draft
    state["dispatch_result"] = {"status": "DISPATCHED", "channel": channel}
    state["status"]          = ExecutionStatus.COMPLETED
    state["execution_trace"] = [build_trace_entry(
        "draft_response_node", int((time.monotonic() - t0) * 1000), 200)]
    state["audit_events"]    = [make_audit_event(
        state, "run_communication_agent", f"COMM_COMPLETE:{channel}")]
    return state