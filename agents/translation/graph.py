from __future__ import annotations
"""agents/translation/graph.py — Translation Agent entry point."""
from shared import (
    BaseAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

from shared.langfuse_manager import get_tracer
from agents.translation.nodes.translation_nodes import (
    detect_language_node, load_glossary_node, preprocess_text_node,
    translate_node, back_translate_node, score_quality_node, format_locale_node,
)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/translation/nodes/ location is preserved for backward compatibility.
from agents.translation.workflows.nodes import (
    detect_language_node, load_glossary_node, preprocess_text_node, translate_node, back_translate_node, score_quality_node, format_locale_node,
)



def run_translation_agent(
    raw_input: str,
    target_language: str = "de",
    source_language: str = None,
    domain: str = "general",
    target_locale: str = None,
    session_id: str = None,
    agent_config: dict = None,
) -> dict:
    """Translate text with quality assurance and locale formatting.

    Consumer config keys (agent_config["prompts"]):
        translate, back_translate, score_quality, format_locale, detect_language, load_glossary

    Consumer config keys (agent_config):
        quality_threshold (float, default 0.75) — below this score, review_required = True
    """
    state = make_base_state(raw_input, AgentType.TRANSLATION, session_id=session_id)
    state.update({
        "target_language": target_language,
        "source_language": source_language,
        "domain": domain,
        "target_locale": target_locale or target_language,
        "glossary": {},
        "protected_terms": [],
        "preprocessed_text": None,
        "translated_text": None,
        "back_translated_text": None,
        "quality_score": None,
        "review_required": False,
        "final_translated_text": None,
        "config": agent_config or {},
    })
    tracer = get_tracer("translation_agent")
    with tracer.trace("translation_workflow", session_id=state["session_id"], input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        state = {**state, **detect_language_node(state)}
        state = {**state, **load_glossary_node(state)}
        state = {**state, **preprocess_text_node(state)}
        state = {**state, **translate_node(state)}
        state = {**state, **back_translate_node(state)}
        state = {**state, **score_quality_node(state)}
        state = {**state, **format_locale_node(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("final_translated_text")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_translation_agent", "AGENT_COMPLETED")
    )
    return state
