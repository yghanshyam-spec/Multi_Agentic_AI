"""
agents/router/prompts/defaults.py
===================================
Built-in prompt defaults for the Router Agent.
These are used as fallbacks when Langfuse prompt registry has no matching entry
and no consumer override has been provided via agent_config.

Consumer override pattern (in use_case_config or agent_config):
    config["agents"]["router"]["prompts"]["analyse_request"] = "Your custom prompt..."
"""
from __future__ import annotations

ANALYSE_REQUEST = (
    "You are an intelligent request router for a multi-agent AI platform.\n"
    "Analyse the user request and determine which agents are needed, execution "
    "priority, and complexity.\n"
    "Available agents: {agents}\n"
    "Return JSON: {{required_agents: [str], parallel_safe: bool, "
    "priority: low|medium|high|critical, estimated_complexity: simple|moderate|complex}}"
)

PLAN_ROUTING = (
    "Given required agents and load metrics, determine optimal routing strategy.\n"
    "Return JSON: {{execution_mode: sequential|parallel|batched, "
    "agent_priority_order: [str], fallback_agents: [str]}}"
)

ORCHESTRATE_RESPONSE = (
    "Multiple agents have returned results for a user request.\n"
    "Synthesise into a single coherent response that directly answers the "
    "user's original request.\n"
    "Return JSON: {{summary: str, presentation_mode: str, key_findings: [str]}}"
)

# Registry — looked up by key in get_default_prompt()
_REGISTRY: dict[str, str] = {
    "router_analyse_request":     ANALYSE_REQUEST,
    "router_plan_routing":        PLAN_ROUTING,
    "router_orchestrate_response": ORCHESTRATE_RESPONSE,
}

AGENT_REGISTRY = [
    "INTENT_AGENT", "PLANNER_AGENT", "WORKFLOW_AGENT",
    "REASONING_AGENT", "GENERATOR_AGENT", "COMMUNICATION_AGENT",
    "EXECUTION_AGENT", "HITL_AGENT", "AUDIT_AGENT",
]


def get_default_prompt(key: str) -> str:
    return _REGISTRY.get(key, "")
