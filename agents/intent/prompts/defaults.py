"""agents/intent/prompts/defaults.py — Built-in prompt defaults."""
CLASSIFY = """You are an intent classification engine for an enterprise AI platform.
Classify the user request into one or more intents from:
[ROUTE_INTENT, CREATE_PLAN, EXECUTE_WORKFLOW, REASON, GENERATE_CONTENT, COMMUNICATE, EXECUTE_SCRIPT, HITL_APPROVAL, AUDIT_LOG, GENERAL_CHAT, UNKNOWN]
Return JSON: {intents: [{intent: str, confidence: float}], primary_intent: str, confidence: [float]}"""

ENTITIES = """Extract structured entities from this request relevant to routing.
Request: {request}
Extract: target_system, incident_type, severity, affected_service, date_range, stakeholders, action_type.
Return JSON with null for absent fields."""

CLARIFY = """The user request is ambiguous. Detected intents: {intents}.
Ask a single, clear clarifying question to disambiguate. Keep it concise."""

AGGREGATE = """Multiple agents have returned results for a compound user request.
Results: {results}
Synthesise into a single coherent, well-structured response addressing the original request."""

_REGISTRY = {
    "intent_classify": CLASSIFY, "intent_entities": ENTITIES,
    "intent_clarify": CLARIFY, "intent_aggregate": AGGREGATE,
}
def get_default_prompt(key: str) -> str: return _REGISTRY.get(key, "")
