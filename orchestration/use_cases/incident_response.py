"""
orchestration/use_cases/incident_response.py
=============================================
Use-case config: Production Incident Response

Steps (in dependency order):
  [Layer 0] router_initial   — Router analyses request + builds routing plan
  [Layer 1] intent           — Classify intent + extract entities
  [Layer 1] planner          — Decompose into executable task plan
  [Layer 2] reasoning        — Root cause analysis with chain-of-thought
  [Layer 3] hitl             — Human approval checkpoint (high-risk action)
  [Layer 3] execution        — Sandbox execution of approved fix
  [Layer 2] generator        — Generate executive incident report
  [Layer 2] communication    — Notify all stakeholders
  [Layer 1] workflow         — Orchestrate and verify workflow completion
  [Layer 3] audit            — Compliance audit of entire pipeline
  [Layer 0] router_final     — Router collects all results + final synthesis

Prompt overrides are set per-agent via agent_config["prompts"].
Consumer teams can override any prompt without touching agent code.
"""
from __future__ import annotations
from orchestration.pipeline import UseCaseConfig, StepDef

USE_CASE_PROMPT = """Critical Production Incident: The Order Processing API latency has spiked 
from 120ms to 4200ms starting at 14:32 UTC. Database CPU is at 94%. 
A deployment (v2.3.1) was made 17 minutes ago. 
The orders table has grown 4x in the last 7 days to 8.2M rows.
Please:
1. Diagnose the root cause using reasoning and evidence analysis
2. Create a remediation plan
3. Get human approval before executing any fix
4. Execute the approved fix in a safe sandbox
5. Generate a full incident report for executives
6. Notify all stakeholders with a professional communication"""


def _router_initial_input(ctx, inp):
    return inp, {}

def _intent_input(ctx, inp):
    return inp, {}

def _planner_input(ctx, inp):
    return inp, {}

def _reasoning_input(ctx, inp):
    return inp, {}

def _hitl_input(ctx, inp):
    reasoning = ctx.get("reasoning", {})
    conclusion = (reasoning.get("conclusion") or {}).get("conclusion", "")
    return (
        "Approve execution of database index fix for production incident",
        {"working_memory": {
            "risk": "high",
            "execution_plan": {
                "script": "CREATE INDEX CONCURRENTLY idx_orders_created_status ON orders(created_at, status)",
                "target": "production_database",
                "expected_outcome": "Query latency < 200ms",
                "rollback": "DROP INDEX CONCURRENTLY idx_orders_created_status",
            },
            "reasoning_conclusion": conclusion,
        }}
    )

def _execution_input(ctx, inp):
    hitl = ctx.get("hitl", {})
    return (
        "Execute approved database index creation",
        {
            "execution_plan": {
                "script": "CREATE INDEX CONCURRENTLY idx_orders_created_status ON orders(created_at, status)",
                "target": "production_database",
                "expected_outcome": "Query latency < 200ms post-execution",
                "rollback": "DROP INDEX CONCURRENTLY idx_orders_created_status",
                "requires_approval": True,
            },
            "approved_by": hitl.get("approver_id", "engineering_lead"),
        }
    )

def _generator_input(ctx, inp):
    reasoning = ctx.get("reasoning", {})
    execution = ctx.get("execution", {})
    return (
        "Generate production incident report for executives",
        {"working_memory": {
            "incident_summary": inp,
            "root_cause": (reasoning.get("conclusion") or {}).get("conclusion",
                "Missing composite index on orders table"),
            "resolution": execution.get("execution_report", "Index created successfully"),
            "timeline": [
                "14:15 UTC — Deployment v2.3.1",
                "14:32 UTC — Alert: API latency > 2000ms",
                "14:48 UTC — Root cause identified (missing index)",
                "15:02 UTC — HITL approval obtained from Engineering Lead",
                "15:04 UTC — Index created CONCURRENTLY (zero downtime)",
                "15:05 UTC — Latency restored ✓",
            ],
            "affected_service": "order_processing_api",
            "business_impact": "~£24,000 in delayed order completions over 32 minutes",
            "reasoning_chain": reasoning.get("reasoning_chain", []),
        }}
    )

def _communication_input(ctx, inp):
    hitl = ctx.get("hitl", {})
    execution = ctx.get("execution", {})
    return (
        "Notify all stakeholders that the production incident has been resolved",
        {"channel": "email", "working_memory": {
            "incident_summary": inp,
            "resolution_status": "RESOLVED",
            "hitl_decision": hitl.get("decision_value", "APPROVED"),
            "exec_report": execution.get("execution_report", ""),
        }}
    )

def _workflow_input(ctx, inp):
    planner = ctx.get("planner", {})
    return inp, {"workflow_plan": planner.get("workflow_plan")}

def _audit_input(ctx, inp):
    all_events = []
    for step_state in ctx.values():
        if isinstance(step_state, dict):
            all_events.extend(step_state.get("audit_events", []))
    return all_events, {}  # passed as first positional arg (all_audit_events)

def _router_final_input(ctx, inp):
    partial = []
    for sid, sstate in ctx.items():
        if isinstance(sstate, dict) and sstate.get("agent_response"):
            partial.append({"agent": sid.upper(), "result": str(sstate.get("agent_response", {}))[:200]})
    return inp, {"partial_results": partial}


INCIDENT_RESPONSE_CONFIG = UseCaseConfig(
    name="Production Incident Response",
    description="Full 10-agent pipeline for diagnosing, remediating, and reporting a production incident.",
    langfuse_tags=["incident-response", "production", "v4"],
    global_config={
        "environment": "production",
        "max_retries": 3,
    },
    steps=[
        StepDef(id="router_initial", agent="router",  label="Router (Initial Analysis)",   layer=0, input_fn=_router_initial_input),
        StepDef(id="intent",         agent="intent",  label="Intent Classification",        layer=1, input_fn=_intent_input,      ),
        StepDef(id="planner",        agent="planner", label="Task Planning",                layer=1, input_fn=_planner_input,     ),
        StepDef(id="reasoning",      agent="reasoning",label="Root Cause Analysis",         layer=2, input_fn=_reasoning_input,   ),
        StepDef(id="hitl",           agent="hitl",    label="Human Approval Checkpoint",    layer=3, input_fn=_hitl_input,        ),
        StepDef(id="execution",      agent="execution",label="Sandbox Execution",           layer=3, input_fn=_execution_input,   ),
        StepDef(id="generator",      agent="generator",label="Incident Report Generation",  layer=2, input_fn=_generator_input,   ),
        StepDef(id="communication",  agent="communication",label="Stakeholder Notification",layer=2, input_fn=_communication_input,),
        StepDef(id="workflow",       agent="workflow", label="Workflow Orchestration",      layer=1, input_fn=_workflow_input,    ),
        StepDef(id="audit",          agent="audit",   label="Compliance Audit",             layer=3, input_fn=_audit_input,       optional=True),
        StepDef(id="router_final",   agent="router",  label="Router (Final Synthesis)",     layer=0, input_fn=_router_final_input),
    ],
)
