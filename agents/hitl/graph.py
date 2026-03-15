"""
agents/hitl/graph.py
=====================
Layer 3 — HITL Agent  |  LangGraph entry-point & pipeline bridge

This file does THREE things:
  1. Registers this folder as the ``agent_hitl`` package so that all existing
     sub-package imports (``from agent_hitl.xxx import ...``) work without any
     changes to the source files you provided.
  2. Assembles a proper ``langgraph.graph.StateGraph`` using the real components
     from the sub-package:
       - workflows/graph_builder.py   → GraphBuilder (agent→checkpoint→human/merge→END)
       - workflows/checkpoint_node.py → CheckpointEvaluator + checkpoint_node
       - ui_adapters/api_adapter.py   → APIAdapter.human_node  (auto-approve, demo)
       - ui_adapters/cli_adapter.py   → CLIAdapter.human_node  (HITL_ADAPTER=cli)
       - ui_adapters/streamlit_adapter.py → StreamlitAdapter.human_node
       - persistence/sqlite_store.py  → SQLiteStore (state persistence)
       - core/resume_handler.py       → ResumeHandler (save/load run state)
       - schemas/graph_state.py       → HITLState TypedDict
       - agents/base_agent.py         → BaseAgent ABC
       - utils/helpers.py             → create_initial_state, generate_run_id
  3. Exposes ``run_hitl_agent()`` which the pipeline uses, bridging the
     accelerator's ``HITLAgentState`` to the sub-package's ``HITLState``.

Full sub-package folder structure (preserved verbatim from agent_hitl):
    agents/hitl/
    ├── graph.py                          ← THIS FILE
    ├── agents/
    │   └── base_agent.py                 BaseAgent ABC (run(state) -> state)
    ├── core/
    │   └── resume_handler.py             ResumeHandler (load_state / save_state)
    ├── persistence/
    │   ├── storage.py                    Storage ABC
    │   └── sqlite_store.py               SQLiteStore(Storage)
    ├── schemas/
    │   ├── graph_state.py                HITLState TypedDict
    │   └── output_models.py              AgentResponse, ErrorResponse (Pydantic)
    ├── ui_adapters/
    │   ├── api_adapter.py                APIAdapter  (auto-approve, demo)
    │   ├── cli_adapter.py                CLIAdapter  (terminal prompt)
    │   └── streamlit_adapter.py          StreamlitAdapter (web UI widget)
    ├── utils/
    │   ├── helpers.py                    create_initial_state, generate_run_id
    │   ├── logger.py, decorators.py, logging_config.py
    └── workflows/
        ├── graph_builder.py              GraphBuilder → StateGraph
        ├── checkpoint_node.py            CheckpointEvaluator + checkpoint_node
        └── nodes/
            ├── process_input.py          process_input_node
            └── format_output.py          format_output_node
"""
from __future__ import annotations

import os
import sys
import types
import time
import uuid

# ── Step 1: register this folder as the ``agent_hitl`` package ───────────────
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

if "agent_hitl" not in sys.modules:
    _pkg = types.ModuleType("agent_hitl")
    _pkg.__path__ = [_THIS_DIR]
    _pkg.__package__ = "agent_hitl"
    _pkg.__spec__ = None
    sys.modules["agent_hitl"] = _pkg

# ── Step 2: LangGraph + shared accelerator imports ───────────────────────────
try:
    from langgraph.graph import StateGraph, END
    _LG_AVAILABLE = True
except ImportError:
    _LG_AVAILABLE = False

from shared import (
        BaseAgentState, AgentMessage, ExecutionMetadata,
HITLAgentState, AgentType, ExecutionStatus, HITLDecision,
    build_agent_response, make_audit_event, utc_now, new_id,
    get_llm, call_llm, build_trace_entry,
)

# ── Step 3: Import the real sub-package components ───────────────────────────
from agent_hitl.schemas.graph_state import HITLState
from agent_hitl.workflows.graph_builder import GraphBuilder
from agent_hitl.workflows.checkpoint_node import CheckpointEvaluator, checkpoint_node
from agent_hitl.persistence.sqlite_store import SQLiteStore
from agent_hitl.persistence.storage import Storage
from agent_hitl.core.resume_handler import ResumeHandler
from agent_hitl.ui_adapters.api_adapter import APIAdapter
from agent_hitl.ui_adapters.cli_adapter import CLIAdapter
from agent_hitl.ui_adapters.streamlit_adapter import StreamlitAdapter
from shared.agents import BaseAgent  # centralised base agent
from agent_hitl.utils.helpers import create_initial_state, generate_run_id
from agent_hitl.utils.logger import get_logger

logger = get_logger(__name__)

# ── Shared persistence (one SQLiteStore per process) ─────────────────────────
_STORE = SQLiteStore(db_path="hitl_runs.db")
_RESUME_HANDLER = ResumeHandler(_STORE)

# ── Default checkpoint config (mirrors config_support.yaml) ──────────────────
_DEFAULT_CHECKPOINT_CONFIG = {
    "configurable": {
        "checkpoints": [
            {
                "name":      "high_risk_score",
                "condition": "state.get('risk_score', 0) > 0.7",
            },
            {
                "name":      "requires_review_flag",
                "condition": "state.get('requires_review', False) == True",
            },
        ]
    }
}


# ═══════════════════════════════════════════════════════════════════════════════
# Accelerator agent wrapper
# Wraps the accelerator's LLM/logic as a BaseAgent so GraphBuilder can use it
# ═══════════════════════════════════════════════════════════════════════════════

class _AcceleratorHITLAgent(BaseAgent):
    """
    Implements BaseAgent.run() using the accelerator's LLM.
    Produces a structured review brief as agent_output for the human approver.
    """

    _SYS_PACKAGE = (
        "Prepare a clear, concise review summary for a human approver. "
        "Context: {context}. "
        "Include: what decision is needed, relevant facts, recommended action, "
        "risk if approved, risk if rejected. Keep under 200 words. "
        "Return JSON: {{review_brief, decision_needed, recommended_action, "
        "risk_if_approved, risk_if_rejected}}"
    )

    def run(self, state: HITLState) -> HITLState:
        llm = get_llm()
        wm  = state.get("extra", {})

        result = call_llm(
            llm,
            self._SYS_PACKAGE.format(context={
                "user_input":         state.get("user_input", ""),
                "risk_score":         state.get("risk_score", 0.0),
                "requires_review":    state.get("requires_review", False),
                "execution_plan":     wm.get("execution_plan", {}),
                "reasoning":          wm.get("reasoning_conclusion", ""),
            }),
            "Package HITL review context",
            node_hint="hitl_package_review",
        )

        brief = result.get("review_brief",
                           result.get("raw_response", "Please review and approve the requested action."))
        return {
            **state,
            "agent_output": brief,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Select the human-node adapter based on HITL_ADAPTER env var
# ═══════════════════════════════════════════════════════════════════════════════

def _get_human_node():
    """
    Returns the human_node function from the appropriate UI adapter.
    HITL_ADAPTER=api (default) → APIAdapter  (auto-approve, demo)
    HITL_ADAPTER=cli           → CLIAdapter  (terminal prompt)
    HITL_ADAPTER=streamlit     → StreamlitAdapter (web widget)
    """
    adapter_name = os.environ.get("HITL_ADAPTER", "api").lower()
    if adapter_name == "cli":
        logger.info("HITL adapter: CLI")
        return CLIAdapter().human_node
    elif adapter_name == "streamlit":
        logger.info("HITL adapter: Streamlit")
        return StreamlitAdapter().human_node
    else:
        logger.info("HITL adapter: API (auto-approve demo)")
        return APIAdapter().human_node


# ═══════════════════════════════════════════════════════════════════════════════
# State translators
# HITLAgentState (accelerator) ↔ HITLState (sub-package)
# ═══════════════════════════════════════════════════════════════════════════════

def _accel_to_hitl(state: HITLAgentState) -> HITLState:
    wm = state.get("working_memory", {})
    risk = wm.get("risk", "high")
    risk_score = wm.get("risk_score",
                        0.9 if risk in ("high", "critical") else
                        0.5 if risk == "medium" else 0.2)
    return HITLState(
        user_input=state.get("raw_input", ""),
        agent_output=None,
        requires_human=False,
        approved=None,
        human_feedback=None,
        checkpoint_name=None,
        metadata={
            "session_id":  state.get("session_id", ""),
            "approver_id": state.get("approver_id", "engineering_lead"),
        },
        history=state.get("partial_results", []),
        risk_score=risk_score,
        requires_review=wm.get("requires_review", False),
        extra=wm,
    )


def _hitl_to_accel_delta(sub_result: HITLState,
                          orig: HITLAgentState) -> dict:
    """Translates the sub-graph HITLState back to accelerator HITLAgentState fields."""
    approved  = sub_result.get("approved", True)
    feedback  = sub_result.get("human_feedback", "")
    cp_name   = sub_result.get("checkpoint_name")

    decision_value = HITLDecision.APPROVED if approved else HITLDecision.REJECTED

    hitl_decision = {
        "value":       decision_value,
        "approver_id": sub_result.get("metadata", {}).get("approver_id", "api_adapter"),
        "timestamp":   utc_now(),
        "notes":       feedback,
        "checkpoint":  cp_name,
    }
    resume_node = "execute_script_node" if approved else "abort_node"

    return {
        "checkpoint_triggered": sub_result.get("requires_human", False),
        "trigger_reason":       f"Checkpoint: {cp_name}" if cp_name else None,
        "review_brief":         sub_result.get("agent_output", ""),
        "hitl_decision":        hitl_decision,
        "decision_value":       decision_value,
        "decision_notes":       feedback,
        "approver_id":          hitl_decision["approver_id"],
        "resume_node":          resume_node,
        "hitl_required":        False,
        "hitl_context": {
            "review_brief":     sub_result.get("agent_output", ""),
            "checkpoint_name":  cp_name,
            "risk_score":       sub_result.get("risk_score", 0.0),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Accelerator-level node functions (wired into the top-level HITLAgentState graph)
# ═══════════════════════════════════════════════════════════════════════════════

def detect_checkpoint_node(state: HITLAgentState) -> dict:
    """
    Evaluates checkpoint rules against working_memory using CheckpointEvaluator.
    Falls back to risk-level heuristic for backward compatibility.
    """
    t0 = time.monotonic()
    wm = state.get("working_memory", {})

    # Build a minimal HITLState for the evaluator
    risk = wm.get("risk", "high")
    risk_score = wm.get("risk_score",
                        0.9 if risk in ("high", "critical") else
                        0.5 if risk == "medium" else 0.2)
    eval_state = HITLState(
        user_input=state.get("raw_input", ""),
        agent_output=None, requires_human=False, approved=None,
        human_feedback=None, checkpoint_name=None,
        metadata={}, history=[], risk_score=risk_score,
        requires_review=wm.get("requires_review", False), extra=wm,
    )

    evaluator = CheckpointEvaluator(_DEFAULT_CHECKPOINT_CONFIG.get("configurable", {}))
    evaluated = evaluator.evaluate(eval_state)

    triggered = evaluated.get("requires_human", False)
    cp_name   = evaluated.get("checkpoint_name")

    # Fallback: legacy risk-level field
    if not triggered:
        triggered = risk in ("high", "critical") or \
                    state.get("feature_flags", {}).get("hitl_enabled", True)
        if triggered:
            cp_name = "high_risk_action"

    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        "checkpoint_triggered": triggered,
        "trigger_reason":       f"Risk: {risk}" if triggered else None,
        "checkpoint_name":      cp_name if triggered else None,
        "status":               ExecutionStatus.RUNNING,
        "current_node":         "detect_checkpoint_node",
        "execution_trace":      [build_trace_entry("detect_checkpoint_node", duration_ms)],
    }


def package_review_context_node(state: HITLAgentState) -> dict:
    """Runs the AcceleratorHITLAgent to produce a structured review brief."""
    t0    = time.monotonic()
    agent = _AcceleratorHITLAgent()
    sub   = _accel_to_hitl(state)
    out   = agent.run(sub)
    brief = out.get("agent_output", "Please review and approve the requested action.")

    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        "review_brief":    brief,
        "hitl_context":    {"review_brief": brief},
        "current_node":    "package_review_context_node",
        "execution_trace": [build_trace_entry("package_review_context_node", duration_ms, 200)],
        "audit_events":    [make_audit_event(state, "package_review_context_node", "HITL_PACKAGED")],
    }


def interrupt_node(state: HITLAgentState) -> dict:
    """
    Pauses workflow: sets PENDING_HUMAN status and persists state via
    ResumeHandler → SQLiteStore (the real sub-package persistence layer).
    """
    t0     = time.monotonic()
    run_id = state.get("run_id", new_id("run"))

    _RESUME_HANDLER.save_state(run_id, {
        "run_id":          run_id,
        "raw_input":       state.get("raw_input", ""),
        "review_brief":    state.get("review_brief", ""),
        "checkpoint_name": state.get("checkpoint_name"),
        "trigger_reason":  state.get("trigger_reason"),
        "paused_at":       utc_now(),
    })

    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        "status":          ExecutionStatus.PENDING_HUMAN,
        "hitl_required":   True,
        "current_node":    "interrupt_node",
        "execution_trace": [build_trace_entry("interrupt_node", duration_ms)],
        "audit_events":    [make_audit_event(state, "interrupt_node", "WORKFLOW_INTERRUPTED")],
    }


def notify_approver_node(state: HITLAgentState) -> dict:
    """Sends structured approval request (mock email with approve/reject deep-links)."""
    t0     = time.monotonic()
    run_id = state.get("run_id", "")
    notification = {
        "recipient":    state.get("approver_id", "engineering_lead@company.com"),
        "channel":      "email",
        "approve_link": f"https://platform.internal/approve/{run_id}",
        "reject_link":  f"https://platform.internal/reject/{run_id}",
        "brief":        state.get("review_brief", ""),
        "checkpoint":   state.get("checkpoint_name", ""),
        "sent_at":      utc_now(),
    }
    logger.info(f"[HITL] Approval request sent to {notification['recipient']}")

    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        "notification_sent": True,
        "current_node":      "notify_approver_node",
        "execution_trace":   [build_trace_entry("notify_approver_node", duration_ms)],
        "audit_events":      [make_audit_event(state, "notify_approver_node", "APPROVER_NOTIFIED")],
    }


def listen_for_response_node(state: HITLAgentState) -> dict:
    """
    Obtains the human decision by running the full GraphBuilder sub-graph
    (agent → checkpoint → human/merge → END) using the selected UI adapter.
    """
    t0 = time.monotonic()

    sub_state  = _accel_to_hitl(state)
    agent      = _AcceleratorHITLAgent()
    human_node = _get_human_node()

    # Use GraphBuilder from sub-package to assemble the decision sub-graph
    builder   = GraphBuilder(
        agent_node=agent.run,
        human_node=human_node,
        config=_DEFAULT_CHECKPOINT_CONFIG,
    )
    sub_graph  = builder.build()
    sub_result = sub_graph.invoke(sub_state)

    delta       = _hitl_to_accel_delta(sub_result, state)
    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        **delta,
        "current_node":    "listen_for_response_node",
        "execution_trace": [build_trace_entry("listen_for_response_node", duration_ms)],
    }


def process_decision_node(state: HITLAgentState) -> dict:
    """Validates and persists the decision via ResumeHandler → SQLiteStore."""
    t0       = time.monotonic()
    decision = state.get("hitl_decision", {})
    value    = decision.get("value", HITLDecision.APPROVED)
    run_id   = state.get("run_id", "")

    saved = _RESUME_HANDLER.load_state(run_id) or {}
    saved.update({
        "decision":    value,
        "approver_id": decision.get("approver_id"),
        "decided_at":  utc_now(),
        "notes":       decision.get("notes"),
    })
    _RESUME_HANDLER.save_state(run_id, saved)

    new_status = (ExecutionStatus.RUNNING if value == HITLDecision.APPROVED
                  else ExecutionStatus.CANCELLED)
    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        "decision_value":  value,
        "status":          new_status,
        "current_node":    "process_decision_node",
        "execution_trace": [build_trace_entry("process_decision_node", duration_ms)],
        "audit_events":    [make_audit_event(
            state, "process_decision_node",
            f"DECISION:{value}:by={decision.get('approver_id')}"
        )],
    }


def resume_workflow_node(state: HITLAgentState) -> dict:
    """Routes to execute_script_node (approved) or abort_node (rejected)."""
    t0          = time.monotonic()
    decision    = state.get("decision_value", HITLDecision.APPROVED)
    resume_node = "execute_script_node" if decision == HITLDecision.APPROVED else "abort_node"

    response = build_agent_response(
        state,
        payload={
            "checkpoint_triggered": state.get("checkpoint_triggered", True),
            "checkpoint_name":      state.get("checkpoint_name"),
            "trigger_reason":       state.get("trigger_reason", ""),
            "review_brief":         state.get("review_brief", ""),
            "decision":             state.get("hitl_decision", {}),
            "decision_value":       decision,
            "resume_node":          resume_node,
            "notification_sent":    state.get("notification_sent", False),
        },
        confidence_score=1.0,   # Human decision = full confidence
    )

    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        "resume_node":     resume_node,
        "hitl_required":   False,
        "agent_response":  dict(response),
        "status":          ExecutionStatus.COMPLETED,
        "current_node":    "resume_workflow_node",
        "execution_trace": [build_trace_entry("resume_workflow_node", duration_ms)],
        "audit_events":    [make_audit_event(
            state, "resume_workflow_node",
            f"WORKFLOW_RESUMED:node={resume_node}"
        )],
    }


def log_hitl_event_node(state: HITLAgentState) -> dict:
    """Writes the complete HITL event record to the audit trail."""
    t0 = time.monotonic()
    hitl_log = {
        "event_type":      "HITL_CHECKPOINT",
        "checkpoint_name": state.get("checkpoint_name"),
        "trigger_reason":  state.get("trigger_reason"),
        "context_sent":    state.get("hitl_context"),
        "review_brief":    state.get("review_brief"),
        "decision":        state.get("hitl_decision"),
        "approver":        state.get("approver_id"),
        "timestamp":       utc_now(),
        "run_id":          state.get("run_id"),
    }
    duration_ms = int((time.monotonic() - t0) * 1000)
    return {
        "current_node":    "log_hitl_event_node",
        "execution_trace": [build_trace_entry("log_hitl_event_node", duration_ms)],
        "audit_events":    [make_audit_event(state, "log_hitl_event_node", "HITL_LOGGED")],
        "partial_results": [hitl_log],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Top-level accelerator LangGraph  (HITLAgentState)
# listen_for_response_node internally invokes GraphBuilder's sub-graph
# (HITLState: agent→checkpoint→human/merge→END)
# ═══════════════════════════════════════════════════════════════════════════════

def build_hitl_graph():
    """
    Returns a compiled langgraph.graph.StateGraph for HITLAgentState.
    listen_for_response_node internally runs GraphBuilder's compiled sub-graph
    (HITLState) which contains the real checkpoint_node, human_node (adapter),
    and merge_node from the sub-package.
    """
    graph = StateGraph(HITLAgentState)

    graph.add_node("detect_checkpoint_node",       detect_checkpoint_node)
    graph.add_node("package_review_context_node",  package_review_context_node)
    graph.add_node("interrupt_node",               interrupt_node)
    graph.add_node("notify_approver_node",          notify_approver_node)
    graph.add_node("listen_for_response_node",     listen_for_response_node)
    graph.add_node("process_decision_node",        process_decision_node)
    graph.add_node("resume_workflow_node",         resume_workflow_node)
    graph.add_node("log_hitl_event_node",          log_hitl_event_node)

    graph.set_entry_point("detect_checkpoint_node")
    graph.add_edge("detect_checkpoint_node",      "package_review_context_node")
    graph.add_edge("package_review_context_node", "interrupt_node")
    graph.add_edge("interrupt_node",              "notify_approver_node")
    graph.add_edge("notify_approver_node",        "listen_for_response_node")
    graph.add_edge("listen_for_response_node",    "process_decision_node")
    graph.add_edge("process_decision_node",       "resume_workflow_node")
    graph.add_edge("resume_workflow_node",        "log_hitl_event_node")
    graph.add_edge("log_hitl_event_node",         END)

    return graph.compile()


# ═══════════════════════════════════════════════════════════════════════════════
# Public runner (called by orchestration/pipeline.py)
# ═══════════════════════════════════════════════════════════════════════════════

def run_hitl_agent(
    raw_input: str,
    working_memory: dict = None,
    session_id: str = None,
) -> dict:
    from shared import make_base_state
    state = make_base_state(raw_input, AgentType.HITL, session_id=session_id)
    # ── Stamp run/correlation IDs for end-to-end Langfuse tracing ────────────
    state.setdefault("run_id", state.get("session_id", ""))
    state.setdefault("correlation_id", state.get("session_id", ""))
    wm = dict(working_memory or {})

    state.update({
        "checkpoint_triggered": False,
        "checkpoint_name":      None,
        "trigger_reason":       None,
        "review_brief":         None,
        "approver_id":          "engineering_lead",
        "decision_value":       HITLDecision.PENDING,
        "decision_notes":       None,
        "resume_node":          None,
        "timeout_seconds":      300,
        "notification_sent":    False,
        "working_memory":       wm,
    })

    compiled = build_hitl_graph()
    return compiled.invoke(state)
