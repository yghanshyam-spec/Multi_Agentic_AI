"""
shared/llm_factory.py
======================
LLM provider abstraction for the entire accelerator.

Routing is controlled entirely by environment variables in the root .env:

    CALL_LLM=false          -> always use MockLLM (default; safe for CI/testing)
    CALL_LLM=true           -> use the real provider selected by LLM_PROVIDER

    LLM_PROVIDER=anthropic  -> ChatAnthropic  (requires ANTHROPIC_API_KEY)
    LLM_PROVIDER=openai     -> ChatOpenAI     (requires OPENAI_API_KEY)
    LLM_PROVIDER=azure_openai -> AzureChatOpenAI (requires AZURE_OPENAI_*)

All agents route EVERY LLM call through this module via:
    from shared.common import get_llm, call_llm

No agent should import or instantiate an LLM class directly.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

# Load root .env exactly once (don't override already-set shell vars)
_ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"
if _ROOT_ENV.exists():
    load_dotenv(_ROOT_ENV, override=False)

try:
    from langchain_anthropic import ChatAnthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI, AzureChatOpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False

try:
    from langchain_core.messages import HumanMessage, SystemMessage
    _LC_AVAILABLE = True
except ImportError:
    _LC_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# ENV HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _call_llm_enabled() -> bool:
    return os.getenv("CALL_LLM", "false").strip().lower() == "true"

def _provider() -> str:
    return os.getenv("LLM_PROVIDER", "anthropic").strip().lower()

def _temperature() -> float:
    return float(os.getenv("LLM_TEMPERATURE", "0.1"))

def _max_tokens() -> int:
    return int(os.getenv("LLM_MAX_TOKENS", "4096"))


# ─────────────────────────────────────────────────────────────────────────────
# MOCK LLM
# ─────────────────────────────────────────────────────────────────────────────

MOCK_RESPONSES: dict = {
    "analyse_request":       {"required_agents": ["INTENT_AGENT","PLANNER_AGENT","REASONING_AGENT"], "parallel_safe": False, "priority": "high", "estimated_complexity": "complex"},
    "plan_routing":          {"execution_mode": "sequential", "agent_priority_order": ["INTENT_AGENT","PLANNER_AGENT","WORKFLOW_AGENT"], "fallback_agents": []},
    "orchestrate_response":  {"summary": "All agents completed successfully.", "presentation_mode": "structured_sections"},
    "classify_intent":       {"intents": [{"intent":"REASON","confidence":0.94},{"intent":"CREATE_PLAN","confidence":0.88}], "primary_intent": "REASON", "confidence": [0.94, 0.88]},
    "extract_entities":      {"target_system":"production_database","incident_type":"performance_degradation","severity":"critical","affected_service":"order_processing_api","stakeholders":["engineering_lead","CTO"]},
    "analyse_goal":          {"objective":"Resolve critical production incident","success_criteria":["Service latency < 200ms","Root cause identified"],"constraints":{"time_budget_minutes":60,"requires_approval":True}},
    "decompose_tasks":       [{"task_id":"T1","title":"Diagnose root cause","agent":"REASONING_AGENT","deps":[],"parallel_safe":False,"risk":"low","description":"Analyse logs","estimated_duration":10},{"task_id":"T2","title":"Remediation plan","agent":"REASONING_AGENT","deps":["T1"],"parallel_safe":False,"risk":"medium","description":"Create steps","estimated_duration":8},{"task_id":"T3","title":"HITL approval","agent":"HITL_AGENT","deps":["T2"],"parallel_safe":False,"risk":"high","description":"Require approval","estimated_duration":5},{"task_id":"T4","title":"Execute fix","agent":"EXECUTION_AGENT","deps":["T3"],"parallel_safe":False,"risk":"high","description":"Apply fix","estimated_duration":5},{"task_id":"T5","title":"Draft report","agent":"GENERATOR_AGENT","deps":["T4"],"parallel_safe":True,"risk":"low","description":"Generate report","estimated_duration":5},{"task_id":"T6","title":"Notify stakeholders","agent":"COMMUNICATION_AGENT","deps":["T5"],"parallel_safe":False,"risk":"low","description":"Send notification","estimated_duration":3}],
    "assign_agents":         {"T1":{"agent_type":"REASONING_AGENT","rationale":"Causal analysis"},"T2":{"agent_type":"REASONING_AGENT","rationale":"Plan generation"},"T3":{"agent_type":"HITL_AGENT","rationale":"Human sign-off"},"T4":{"agent_type":"EXECUTION_AGENT","rationale":"Sandboxed execution"},"T5":{"agent_type":"GENERATOR_AGENT","rationale":"Report generation"},"T6":{"agent_type":"COMMUNICATION_AGENT","rationale":"Multi-channel notification"}},
    "validate_plan":         {"valid": True, "gaps": [], "recommendations": ["Consider parallel execution of T5 during T4"]},
    "frame_problem":         {"core_question":"Why did order_processing_api latency spike?","known_facts":["Deployment v2.3.1 at 14:15 UTC","DB CPU at 94%","orders table 8.2M rows"],"unknowns":["Whether slow query is sole cause"],"constraints":["RTO = 30 minutes"]},
    "generate_hypotheses":   [{"id":"H1","statement":"Missing index causing full table scan","supporting_evidence":["DB CPU 94%","Seq Scan in query plan"],"contradicting_evidence":[]},{"id":"H2","statement":"N+1 query pattern in v2.3.1","supporting_evidence":["Deployment timestamp matches spike"],"contradicting_evidence":["DB pool not exhausted"]}],
    "evaluate_evidence":     {"H1":{"support_score":0.91,"confidence":"high","key_gaps":[]},"H2":{"support_score":0.43,"confidence":"low","key_gaps":["Need query count per request"]}},
    "chain_of_thought":      {"steps":["Step 1: Deployment preceded spike by 17 min.","Step 2: orders table grew 4x — query planner switched to sequential scan.","Step 3: EXPLAIN ANALYZE confirms Seq Scan (cost=0..89432).","Step 4: Index reduces scan cost. Estimated: 4200ms -> 85ms.","Step 5: H1 confirmed. H2 ruled out."],"primary_cause":"H1","confidence":0.93},
    "synthesise_conclusion": {"conclusion":"Root cause: missing composite index on orders(created_at, status). Fix: CREATE INDEX CONCURRENTLY.","confidence":0.93,"confidence_level":"high","key_assumptions":["No other slow queries"],"alternative_interpretations":["N+1 pattern may exist but not primary"]},
    "validate_reasoning":    {"valid": True, "issues": [], "severity": "low"},
    "select_template":       {"template_id":"incident_report_v2","rationale":"Production incident template","required_inputs":["timeline","root_cause","resolution_steps"]},
    "plan_content":          {"sections":[{"id":"exec_summary","title":"Executive Summary","key_points":["Overview","Business impact"]},{"id":"timeline","title":"Incident Timeline","key_points":["14:15 Deployment","14:32 Alert","15:04 Resolution"]},{"id":"root_cause","title":"Root Cause Analysis","key_points":["Missing index","Table growth"]},{"id":"resolution","title":"Resolution","key_points":["Index creation","Monitoring alerts"]}]},
    "generate_section":      "## Executive Summary\n\nOn 15 January 2025, the Order Processing API experienced a critical latency spike from 120ms to 4,200ms for 32 minutes.\n\nRoot cause: missing composite index on the orders table.\nResolution: CREATE INDEX CONCURRENTLY — zero downtime.\n\n**Status: RESOLVED**",
    "review_content":        {"score": 9, "issues": [], "revision_needed": False},
    "classify_message":      {"message_type":"incident_notification","urgency":"high","requires_human":False,"handling_path":"automated_response"},
    "draft_response":        "Subject: RESOLVED — Production Incident\n\nDear Team,\n\nThe production incident has been fully resolved.\n\nRoot Cause: Missing composite index on orders table.\nResolution: Index created concurrently with zero downtime.\n\nRegards,\nAgentic AI Operations Platform",
    "check_consistency":     {"consistent": True, "issues": []},
    "validate_preconditions":{"safe_to_execute": True, "blockers": [], "environment_ready": True},
    "verify_output":         {"success": True, "match_score": 0.97, "anomalies": [], "action": "continue"},
    "report_execution":      "Execution completed.\n\nScript: CREATE INDEX CONCURRENTLY idx_orders_created_status\nDuration: 18.3s | Rows: 8,200,000 | Status: SUCCESS\nPost-verification: Query latency 87ms (target <200ms)",
    "package_review_context":{"review_brief":"Engineering Lead approval required before executing DB index on production.","decision_needed":"Approve or Reject: CREATE INDEX CONCURRENTLY","risk_if_approved":"Minimal — no table lock","risk_if_rejected":"SLA breach in ~20 min","recommended_action":"APPROVE"},
    "evaluate_policy":       {"compliant": True, "violations": []},
    "detect_anomalies":      {"anomalies_found": False, "anomalies": [], "baseline_match": True},
    "auto_orchestrate": {
        "use_case_title": "Automated Request Pipeline",
        "reasoning": "LLM selected agents based on request complexity and domain requirements.",
        "agents": [
            {"agent": "intent",       "label": "Intent Classification",      "layer": 1, "deps": [],              "optional": False},
            {"agent": "reasoning",    "label": "Analysis & Reasoning",       "layer": 2, "deps": ["intent"],      "optional": False},
            {"agent": "generator",    "label": "Response Generation",        "layer": 2, "deps": ["reasoning"],   "optional": False},
            {"agent": "communication","label": "Stakeholder Notification",   "layer": 2, "deps": ["generator"],   "optional": False},
            {"agent": "audit",        "label": "Compliance Audit",           "layer": 3, "deps": ["communication"],"optional": True},
        ]
    },
    "generate_audit_report": {"total_events":14,"llm_calls":8,"total_tokens_used":4820,"policy_violations":0,"anomalies_detected":0,"compliance_score":1.0,"agents_involved":["ROUTER_AGENT","INTENT_AGENT","PLANNER_AGENT","REASONING_AGENT","GENERATOR_AGENT","COMMUNICATION_AGENT","EXECUTION_AGENT","HITL_AGENT","AUDIT_AGENT"],"hitl_checkpoints":1,"hitl_decisions":[{"node":"HITL_AGENT","decision":"APPROVED","approver":"engineering_lead"}]},
}


def get_mock_response(node_hint: str, prompt: str = "") -> dict:
    for key, val in MOCK_RESPONSES.items():
        if key in node_hint.lower() or node_hint.lower() in key:
            return val if isinstance(val, dict) else {"result": val}
    return {"result": f"Mock response for '{node_hint}'", "status": "completed", "confidence": 0.85}


class MockLLMResponse:
    def __init__(self, content: str):
        self.content = content


class MockLLM:
    """Deterministic mock LLM — used when CALL_LLM=false."""
    def __init__(self, model: str = "mock"):
        self.model_name = model

    def invoke(self, messages, **kwargs) -> MockLLMResponse:
        prompt = ""
        system_content = ""
        if isinstance(messages, list):
            for m in reversed(messages):
                if hasattr(m, "content"):
                    prompt = str(m.content); break
                elif isinstance(m, dict) and m.get("role") == "user":
                    prompt = str(m.get("content", "")); break
            for m in messages:
                if hasattr(m, "type") and m.type == "system":
                    system_content = m.content.lower()
                elif isinstance(m, dict) and m.get("role") == "system":
                    system_content = m.get("content", "").lower()

        combined = system_content + " " + prompt.lower()
        node_hint = self._detect_node(combined)
        result = get_mock_response(node_hint, prompt)
        return MockLLMResponse(content=json.dumps(result, indent=2))

    def _detect_node(self, combined: str) -> str:
        patterns = {
            "analyse_request":        [r"analyse.*request", r"required.*agent"],
            "plan_routing":           [r"routing.*strateg", r"execution.*mode"],
            "orchestrate_response":   [r"orchestrat", r"unified.*response"],
            "classify_intent":        [r"classif.*intent"],
            "extract_entities":       [r"extract.*entit"],
            "analyse_goal":           [r"analys.*goal", r"success.*criteria"],
            "decompose_tasks":        [r"decompose", r"task.*break"],
            "assign_agents":          [r"assign.*agent"],
            "validate_plan":          [r"validate.*plan"],
            "frame_problem":          [r"core.*question", r"frame.*problem"],
            "generate_hypotheses":    [r"hypothes"],
            "evaluate_evidence":      [r"evaluat.*evidence"],
            "chain_of_thought":       [r"step.*by.*step", r"reasoning.*chain"],
            "synthesise_conclusion":  [r"final.*conclus"],
            "validate_reasoning":     [r"logical.*fallac"],
            "select_template":        [r"template.*select"],
            "plan_content":           [r"content.*outline"],
            "generate_section":       [r"write.*section"],
            "review_content":         [r"quality.*gate"],
            "classify_message":       [r"classif.*message"],
            "draft_response":         [r"draft.*response", r"draft.*reply"],
            "check_consistency":      [r"consistency"],
            "validate_preconditions": [r"precondition"],
            "verify_output":          [r"verify.*output"],
            "report_execution":       [r"execution.*summary"],
            "package_review_context": [r"hitl", r"human.*approver"],
            "evaluate_policy":        [r"policy.*ruleset"],
            "detect_anomalies":       [r"anomal"],
            "generate_audit_report":  [r"audit.*report"],
            "auto_orchestrate":       [r"orchestration.*planner", r"select.*agent", r"minimum.*set.*agent"],
        }
        for node, pats in patterns.items():
            if any(re.search(p, combined) for p in pats):
                return node
        return "generic"

    async def ainvoke(self, messages, **kwargs) -> MockLLMResponse:
        return self.invoke(messages, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC FACTORY
# ─────────────────────────────────────────────────────────────────────────────

def get_llm(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> Any:
    """
    Return the correct LLM based on .env configuration.

    CALL_LLM=false (default) -> MockLLM — no API key required
    CALL_LLM=true            -> real provider via LLM_PROVIDER

    All agents call this function — never instantiate LLM classes directly.
    """
    temp   = temperature if temperature is not None else _temperature()
    tokens = max_tokens  if max_tokens  is not None else _max_tokens()

    if not _call_llm_enabled():
        return MockLLM(model="mock")

    provider = _provider()

    if provider == "anthropic":
        if not _ANTHROPIC_AVAILABLE:
            raise ImportError("langchain-anthropic not installed. Run: pip install langchain-anthropic")
        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            temperature=temp,
            max_tokens=tokens,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

    if provider == "openai":
        if not _OPENAI_AVAILABLE:
            raise ImportError("langchain-openai not installed. Run: pip install langchain-openai")
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=temp,
            max_tokens=tokens,
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    if provider == "azure_openai":
        if not _OPENAI_AVAILABLE:
            raise ImportError("langchain-openai not installed. Run: pip install langchain-openai")
        return AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            temperature=temp,
            max_tokens=tokens,
        )

    raise ValueError(
        f"Unknown LLM_PROVIDER='{provider}'. "
        "Valid options: 'anthropic', 'openai', 'azure_openai'."
    )


def call_llm(llm: Any, system_prompt: str, user_prompt: str, node_hint: str = "") -> dict:
    """
    Invoke *llm* and always return a dict.
    All agents MUST use this function — never call llm.invoke() directly.

    The returned dict always contains:
      - The parsed JSON keys from the LLM response, OR
      - {"raw_response": ..., "parsed": False}  if JSON parsing fails, OR
      - {"error": ..., "node_hint": ...}         on exception

    Token usage is stored in the shared module-level _LAST_TOKEN_USAGE so that
    log_llm_call() can read it immediately after this function returns.
    """
    global _LAST_TOKEN_USAGE
    _LAST_TOKEN_USAGE = {}
    try:
        if _LC_AVAILABLE:
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        else:
            messages = [{"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt}]

        response = llm.invoke(messages)

        # Extract token usage from real LLM responses (Anthropic / OpenAI)
        usage = getattr(response, "usage_metadata", None) or \
                getattr(response, "response_metadata", {}).get("usage", {}) or {}
        if usage:
            _LAST_TOKEN_USAGE = {
                "input":  int(getattr(usage, "input_tokens",  0) or usage.get("input_tokens",  0) or usage.get("prompt_tokens", 0)),
                "output": int(getattr(usage, "output_tokens", 0) or usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)),
            }

        raw = response.content if hasattr(response, "content") else str(response)
        raw_stripped = raw.strip()
        if raw_stripped.startswith("```"):
            raw_stripped = re.sub(r"```(?:json)?", "", raw_stripped).strip("`").strip()
        try:
            return json.loads(raw_stripped)
        except json.JSONDecodeError:
            return {"raw_response": raw, "parsed": False}
    except Exception as exc:
        return {"error": str(exc), "node_hint": node_hint}


# Module-level slot for the token usage of the most recent call_llm() call.
# Read immediately after call_llm() to pass to log_llm_call().
_LAST_TOKEN_USAGE: dict = {}


def get_last_token_usage() -> dict:
    """Return token usage from the most recent call_llm() call."""
    return dict(_LAST_TOKEN_USAGE)
