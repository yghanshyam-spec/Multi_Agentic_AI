"""
orchestration/auto_orchestrator.py
====================================
Generalised Auto-Orchestration Layer.

Automatically identifies the ordered execution sequence of agents from a
natural-language user request — no hand-written StepDef lists required.

How it works
------------
1. ``analyse_request(user_input)``
   → Uses the Router + Intent agents (or the shared LLM directly) to produce
     a ranked list of required agents with dependency annotations.

2. ``build_auto_pipeline(user_input, ...)``
   → Calls ``analyse_request()``, maps agent names to ``StepDef`` objects,
     resolves dependencies via topological sort, and returns a ``UseCaseConfig``
     ready for ``run_pipeline()``.

3. ``run_auto(user_input, ...)``
   → Full end-to-end: analyse → build pipeline → run → return ``PipelineResult``
     with a human-readable execution summary.

Agent Selection Heuristics
--------------------------
The LLM (via ``shared.llm_factory``) classifies the request and returns a JSON
plan with these fields::

    {
      "use_case_title": "...",
      "agents": [
        {
          "agent":  "reasoning",      # key from AGENT_REGISTRY
          "label":  "Root Cause Analysis",
          "layer":  2,
          "deps":   ["intent", "planner"],
          "reason": "Need causal analysis before acting"
        },
        ...
      ]
    }

The full AGENT_REGISTRY (21 agents) and their capabilities are injected into
the system prompt so the LLM can make informed routing decisions.

Environment / .env
------------------
The same ``CALL_LLM`` / ``LLM_PROVIDER`` variables control whether the
auto-orchestrator uses a real LLM or the built-in ``MockLLM``.
``LANGFUSE_ENABLED`` controls tracing of the orchestration analysis step.

Usage
-----
    from orchestration.auto_orchestrator import run_auto, build_auto_pipeline

    # Fully automatic — no StepDef authoring required:
    result = run_auto("Generate a Japanese market report for Nomura Capital")
    print(result.summary)

    # Semi-automatic — inspect the plan before running:
    cfg = build_auto_pipeline("Resolve the prod incident on the orders API")
    for step in cfg.steps:
        print(f"  [{step.layer}] {step.agent} — {step.label}")
    result = run_pipeline(cfg, user_input)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from shared.llm_factory import get_llm, call_llm
from shared.langfuse_manager import get_tracer, log_llm_call
from shared.utils.logger import get_logger
from shared import utc_now

from orchestration.pipeline import (
    UseCaseConfig, StepDef, PipelineResult, run_pipeline, _topo_sort,
)

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# AGENT CAPABILITY REGISTRY
# ─────────────────────────────────────────────────────────────────────────────
# Each entry describes what the agent does, its layer, and typical dependencies.
# This is injected into the LLM system prompt for agent selection.

AGENT_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "router": {
        "description": "Entry/exit point. Dispatches request to specialist agents. Synthesises final response.",
        "layer": 0,
        "typical_deps": [],
        "use_when": ["multi-agent dispatch", "final synthesis", "request routing"],
    },
    "intent": {
        "description": "Classifies user intent, extracts entities, identifies sub-tasks.",
        "layer": 1,
        "typical_deps": ["router"],
        "use_when": ["intent classification", "entity extraction", "NLU"],
    },
    "planner": {
        "description": "Decomposes a high-level goal into sequenced, dependency-aware tasks.",
        "layer": 1,
        "typical_deps": ["intent"],
        "use_when": ["task decomposition", "multi-step planning", "workflow design"],
    },
    "workflow": {
        "description": "Orchestrates and monitors execution of a multi-step plan.",
        "layer": 1,
        "typical_deps": ["planner"],
        "use_when": ["workflow execution", "step sequencing", "parallel orchestration"],
    },
    "reasoning": {
        "description": "Chain-of-thought reasoning, root cause analysis, hypothesis evaluation.",
        "layer": 2,
        "typical_deps": ["planner"],
        "use_when": ["root cause analysis", "evidence evaluation", "decision support"],
    },
    "generator": {
        "description": "Generates structured documents, reports, and proposals from templates.",
        "layer": 2,
        "typical_deps": ["reasoning"],
        "use_when": ["report generation", "document drafting", "proposal writing"],
    },
    "communication": {
        "description": "Omnichannel message drafting and delivery (email, Slack, chat, webhook).",
        "layer": 2,
        "typical_deps": [],
        "use_when": ["send email", "notify stakeholders", "omnichannel dispatch"],
    },
    "translation": {
        "description": "Language detection and bidirectional translation across 50+ languages.",
        "layer": 2,
        "typical_deps": [],
        "use_when": ["translate", "multilingual", "localise", "language detection"],
    },
    "hitl": {
        "description": "Human-in-the-Loop approval checkpoint. Pauses pipeline for human decision.",
        "layer": 3,
        "typical_deps": ["reasoning"],
        "use_when": ["approval required", "human review", "high-risk action"],
    },
    "execution": {
        "description": "Sandboxed script/command execution with pre/post verification.",
        "layer": 3,
        "typical_deps": ["hitl"],
        "use_when": ["execute script", "run command", "apply fix", "provisioning"],
    },
    "audit": {
        "description": "Compliance audit — logs all events, detects policy violations, scores compliance.",
        "layer": 3,
        "typical_deps": [],
        "use_when": ["compliance", "audit trail", "SOX", "policy enforcement"],
    },
    "email_handler": {
        "description": "Parses inbound emails, extracts structured data, classifies message type.",
        "layer": 1,
        "typical_deps": [],
        "use_when": ["parse email", "inbound email", "email classification"],
    },
    "pdf_ingestor": {
        "description": "Ingests PDF documents into a vector store for RAG retrieval.",
        "layer": 1,
        "typical_deps": [],
        "use_when": ["ingest PDF", "document ingestion", "index document"],
    },
    "vector_query": {
        "description": "Semantic search (RAG) over ingested document stores.",
        "layer": 2,
        "typical_deps": ["pdf_ingestor"],
        "use_when": ["search knowledge base", "RAG", "document Q&A", "semantic search"],
    },
    "sql": {
        "description": "Natural language to SQL query generation and execution.",
        "layer": 1,
        "typical_deps": [],
        "use_when": ["query database", "SQL", "analytics", "data retrieval"],
    },
    "api_query": {
        "description": "Calls external REST APIs using OpenAPI specs with auth management.",
        "layer": 1,
        "typical_deps": [],
        "use_when": ["external API", "REST call", "market data", "third-party integration"],
    },
    "mcp_invoker": {
        "description": "Invokes MCP (Model Context Protocol) tools — web search, system tools, etc.",
        "layer": 1,
        "typical_deps": [],
        "use_when": ["web search", "MCP tool", "external tool", "browse web"],
    },
    "salesforce": {
        "description": "Reads and writes Salesforce CRM data (Opportunities, Accounts, Cases).",
        "layer": 1,
        "typical_deps": [],
        "use_when": ["Salesforce", "CRM", "pipeline data", "opportunities"],
    },
    "sap": {
        "description": "Integrates with SAP modules (MM, FI, HR, SD) via BAPI/RFC calls.",
        "layer": 2,
        "typical_deps": [],
        "use_when": ["SAP", "ERP", "PO", "goods receipt", "employee record", "financial posting"],
    },
    "notification": {
        "description": "Sends real-time event-driven notifications via multiple channels.",
        "layer": 2,
        "typical_deps": [],
        "use_when": ["notification", "alert", "push notification", "event-driven update"],
    },
    "scheduling": {
        "description": "Manages calendar scheduling — check availability, create events.",
        "layer": 2,
        "typical_deps": [],
        "use_when": ["schedule meeting", "book calendar", "calendar event", "Teams/Zoom"],
    },
}

_SYSTEM_PROMPT = """You are an expert AI orchestration planner.

Given a user request, you must select the minimum set of agents needed to fulfil it
and specify their execution order with dependencies.

Available agents and their capabilities:
{agent_catalogue}

Rules:
1. Only select agents that are ACTUALLY needed for this request.
2. Assign layer (0=entry/exit, 1=data_gather, 2=process/generate, 3=execute/govern).
3. Specify deps as a list of agent keys that must complete BEFORE this agent runs.
4. Keep deps minimal — only hard dependencies, not soft ordering preferences.
5. Always include "audit" as the LAST optional step (layer=3, PLACEHOLDER).
6. Always return valid JSON only — no prose, no markdown code blocks.

Return EXACTLY this JSON structure:
{{
  "use_case_title": "<descriptive title for this pipeline>",
  "reasoning": "<one sentence explaining the agent selection>",
  "agents": [
    {{
      "agent": "<agent_key>",
      "label": "<human readable step label>",
      "layer": <0-3>,
      "deps": ["<agent_key>", ...],
      "optional": false,
      "reason": "<why this agent is needed>"
    }}
  ]
}}"""

_USER_PROMPT_TEMPLATE = """User request:
{user_input}

Analyse this request and select the appropriate agents in the correct execution order.
Return only JSON."""


# ─────────────────────────────────────────────────────────────────────────────
# ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AgentPlan:
    """Structured output from the auto-analysis step."""
    use_case_title: str
    reasoning: str
    agents: List[Dict[str, Any]]
    raw_llm_output: str = ""


def analyse_request(user_input: str, session_id: str = "") -> AgentPlan:
    """
    Use the LLM to analyse ``user_input`` and produce an ordered agent plan.

    Returns an ``AgentPlan`` dataclass.  Falls back to a sensible default
    (intent → reasoning → generator → audit) if the LLM fails to return
    valid JSON.
    """
    tracer = get_tracer("auto_orchestrator")

    # Build the system prompt with the agent catalogue embedded
    catalogue_lines = []
    for key, caps in AGENT_CAPABILITIES.items():
        deps_str = ", ".join(caps["typical_deps"]) or "none"
        use_when = "; ".join(caps["use_when"])
        catalogue_lines.append(
            f'  "{key}" (layer {caps["layer"]}, typical_PLACEHOLDER): '
            f'{caps["description"]} | Use when: {use_when}'
        )
    catalogue = "\n".join(catalogue_lines)

    system_prompt = _SYSTEM_PROMPT.format(agent_catalogue=catalogue)
    user_prompt   = _USER_PROMPT_TEMPLATE.format(user_input=user_input[:2000])

    llm = get_llm()

    with tracer.trace("auto_orchestrator.analyse", session_id=session_id, input=user_input[:300]):
        raw = call_llm(llm, system_prompt, user_prompt, node_hint="auto_orchestrator_analyse")

    log_llm_call(
        agent_name="auto_orchestrator",
        node_name="analyse_request",
        model=getattr(llm, "model_name", "mock"),
        prompt=system_prompt[:300],
        response=str(raw)[:500],
        session_id=session_id,
    )

    # raw is already parsed by call_llm()
    if isinstance(raw, dict) and "agents" in raw:
        return AgentPlan(
            use_case_title=raw.get("use_case_title", "Auto-Orchestrated Pipeline"),
            reasoning=raw.get("reasoning", ""),
            agents=raw.get("agents", []),
            raw_llm_output=json.dumps(raw),
        )

    # Fallback: minimal safe pipeline
    logger.warning("[AutoOrchestrator] LLM did not return valid plan; using fallback pipeline.")
    return _fallback_plan(user_input)


def _fallback_plan(user_input: str) -> AgentPlan:
    """Minimal safe fallback if LLM analysis fails."""
    return AgentPlan(
        use_case_title="Auto-Orchestrated Request",
        reasoning="Fallback pipeline: intent classification → reasoning → generation → audit.",
        agents=[
            {"agent": "intent",    "label": "Intent Classification", "layer": 1, "deps": [],          "optional": False},
            {"agent": "reasoning", "label": "Analysis & Reasoning",  "layer": 2, "deps": ["intent"],  "optional": False},
            {"agent": "generator", "label": "Response Generation",   "layer": 2, "deps": ["reasoning"],"optional": False},
            {"agent": "audit",     "label": "Compliance Audit",      "layer": 3, "deps": ["generator"],"optional": True},
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def build_auto_pipeline(
    user_input: str,
    session_id: str = "",
    global_config: Dict[str, Any] = None,
    plan: AgentPlan = None,
) -> UseCaseConfig:
    """
    Analyse ``user_input`` and build a ``UseCaseConfig`` automatically.

    Parameters
    ----------
    user_input    : natural language request
    session_id    : optional trace/correlation ID
    global_config : optional shared config injected into every agent
    plan          : optional pre-computed AgentPlan (skip LLM analysis if provided)

    Returns
    -------
    UseCaseConfig — ready to pass to ``run_pipeline()``
    """
    if plan is None:
        plan = analyse_request(user_input, session_id=session_id)

    # Validate and filter to known agents
    known_agents = set(AGENT_CAPABILITIES.keys())
    valid_agent_defs = [a for a in plan.agents if a.get("agent") in known_agents]

    if not valid_agent_defs:
        logger.warning("[AutoOrchestrator] No valid agents in plan; using fallback.")
        plan = _fallback_plan(user_input)
        valid_agent_defs = plan.agents

    # Build step IDs — handle duplicate agent keys (e.g. translation used twice)
    step_id_counter: Dict[str, int] = {}
    steps: List[StepDef] = []

    for agent_def in valid_agent_defs:
        agent_key = agent_def["agent"]
        step_id_counter[agent_key] = step_id_counter.get(agent_key, 0) + 1
        count = step_id_counter[agent_key]
        step_id = agent_key if count == 1 else f"{agent_key}_{count}"

        # Resolve deps — remap agent_key deps to step IDs (use first occurrence)
        raw_deps = agent_def.get("deps", [])
        resolved_deps = []
        for dep_key in raw_deps:
            # Use first occurrence of dep agent
            resolved_deps.append(dep_key)  # step_id of first occurrence = agent_key

        layer     = agent_def.get("layer", AGENT_CAPABILITIES.get(agent_key, {}).get("layer", 2))
        label     = agent_def.get("label", agent_key.replace("_", " ").title())
        optional  = agent_def.get("optional", False)

        steps.append(StepDef(
            id=step_id,
            agent=agent_key,
            label=label,
            layer=layer,
            deps=resolved_deps,
            optional=optional,
            input_fn=_make_passthrough_input(agent_key),
        ))

    return UseCaseConfig(
        name=plan.use_case_title,
        description=(
            f"Auto-orchestrated pipeline. Analysis: {plan.reasoning} "
            f"Agents selected: {', '.join(s.agent for s in steps)}."
        ),
        steps=steps,
        global_config=global_config or {},
        langfuse_tags=["auto-orchestrated", "v4"],
    )


# ── Smart per-agent input_fn defaults ────────────────────────────────────────

def _make_audit_input():
    """Audit agent expects (list_of_events, {}) — collect from pipeline context."""
    def input_fn(ctx, raw_input):
        events = []
        for s in ctx.values():
            if isinstance(s, dict):
                events.extend(s.get("audit_events", []))
        return events, {}
    input_fn.__name__ = "auto_audit_input"
    return input_fn


def _make_passthrough_input(agent_key: str):
    """
    Return a default input_fn that passes the raw user input through.
    Audit gets a smart collector instead of passthrough.
    """
    if agent_key == "audit":
        return _make_audit_input()

    def input_fn(ctx, raw_input):
        return raw_input, {}
    input_fn.__name__ = f"passthrough_{agent_key}"
    return input_fn


# ─────────────────────────────────────────────────────────────────────────────
# FINAL RESPONSE SYNTHESISER
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AutoPipelineResult:
    """Extended result with auto-orchestration metadata and human-readable summary."""
    pipeline_result: PipelineResult
    plan:            AgentPlan
    summary:         str
    execution_order: List[str]
    steps_completed: int
    steps_failed:    int
    total_ms:        int


def _synthesise_summary(result: PipelineResult, plan: AgentPlan) -> str:
    """Build a human-readable execution summary from the pipeline result."""
    completed = [s for s in result.steps if s.status == "COMPLETED"]
    failed    = [s for s in result.steps if s.status == "FAILED"]

    lines = [
        f"# Auto-Orchestrated Pipeline: {result.use_case}",
        f"**Session**: {result.session_id}  |  **Total time**: {result.total_duration_ms}ms",
        f"**Steps**: {len(completed)} completed / {len(failed)} failed",
        "",
        f"**Planning rationale**: {plan.reasoning}",
        "",
        "## Execution Order",
    ]

    for step in result.steps:
        icon   = "✓" if step.status == "COMPLETED" else "✗"
        key_out = ""
        ko = step.key_output
        if ko:
            top = list(ko.items())[:2]
            key_out = "  →  " + ", ".join(f"{k}={v}" for k, v in top if v)
        lines.append(f"  [{step.layer}] {icon} **{step.step_label}** (`{step.agent}`){key_out}")

    if result.all_audit_events:
        lines += ["", f"**Audit events**: {len(result.all_audit_events)} logged"]

    if failed:
        lines += ["", "## Failures"]
        for s in failed:
            lines.append(f"  - `{s.step_id}` ({s.agent}): {s.error or 'unknown error'}")

    lines += [
        "",
        "## Final Outputs",
    ]
    for step_id, out in result.final_output.items():
        if out:
            lines.append(f"  - **{step_id}**: {str(out)[:200]}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# TOP-LEVEL ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def run_auto(
    user_input: str,
    session_id: str = "",
    global_config: Dict[str, Any] = None,
    on_step=None,
    verbose: bool = True,
) -> AutoPipelineResult:
    """
    Fully automatic pipeline: analyse intent → build pipeline → execute → summarise.

    Parameters
    ----------
    user_input    : natural language request
    session_id    : optional correlation ID
    global_config : optional shared config for all agents
    on_step       : optional StepCallback for progress events
    verbose       : if True, log the execution plan to stdout before running

    Returns
    -------
    AutoPipelineResult — contains PipelineResult + human-readable summary
    """
    from shared import new_id
    sid = session_id or new_id("auto")

    logger.info(f"[AutoOrchestrator] Analysing request: {user_input[:100]}...")
    plan = analyse_request(user_input, session_id=sid)

    use_case_cfg = build_auto_pipeline(
        user_input,
        session_id=sid,
        global_config=global_config,
        plan=plan,
    )

    if verbose:
        order = " → ".join(s.agent for s in use_case_cfg.steps)
        logger.info(f"[AutoOrchestrator] Plan: {plan.use_case_title}")
        logger.info(f"[AutoOrchestrator] Execution order: {order}")
        print(f"\n{'='*65}")
        print(f"Auto-Orchestrated Pipeline: {plan.use_case_title}")
        print(f"Rationale: {plan.reasoning}")
        print(f"Agents ({len(use_case_cfg.steps)}): {order}")
        print(f"{'='*65}\n")

    result = run_pipeline(use_case_cfg, user_input, session_id=sid, on_step=on_step)

    summary = _synthesise_summary(result, plan)
    execution_order = [s.agent for s in result.steps]

    return AutoPipelineResult(
        pipeline_result=result,
        plan=plan,
        summary=summary,
        execution_order=execution_order,
        steps_completed=sum(1 for s in result.steps if s.status == "COMPLETED"),
        steps_failed=sum(1 for s in result.steps if s.status == "FAILED"),
        total_ms=result.total_duration_ms,
    )


# ─────────────────────────────────────────────────────────────────────────────
# PLAN INSPECTOR (developer utility)
# ─────────────────────────────────────────────────────────────────────────────

def inspect_plan(user_input: str) -> str:
    """
    Returns a human-readable execution plan WITHOUT running it.
    Useful for previewing what the orchestrator would do.

    Usage::
        print(inspect_plan("Translate the incident report to Japanese and email to the CTO"))
    """
    plan = analyse_request(user_input)
    cfg  = build_auto_pipeline(user_input, plan=plan)
    sorted_steps = _topo_sort(cfg.steps)

    lines = [
        f"Auto-Orchestration Plan: {plan.use_case_title}",
        f"Rationale: {plan.reasoning}",
        f"Steps ({len(sorted_steps)}):",
    ]
    for i, step in enumerate(sorted_steps, 1):
        deps_str = f"  ← deps: [{', '.join(step.deps)}]" if step.deps else ""
        opt_str  = "  (optional)" if step.optional else ""
        cap      = AGENT_CAPABILITIES.get(step.agent, {})
        lines.append(
            f"  {i:2}. [{step.layer}] {step.agent:20} | {step.label}{deps_str}{opt_str}"
        )
        if cap.get("description"):
            lines.append(f"         └─ {cap['description'][:80]}")

    return "\n".join(lines)
