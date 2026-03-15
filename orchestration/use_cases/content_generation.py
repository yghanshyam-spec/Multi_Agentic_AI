"""
orchestration/use_cases/content_generation.py
===============================================
Use-case config: Content Generation Pipeline

A simpler use case that demonstrates the generalized pipeline with only
4 agents (no execution/HITL). Shows how the same orchestration layer
serves entirely different workflows.

Steps:
  [Layer 0] router       — Route and analyse content request
  [Layer 1] intent       — Classify content type and extract parameters
  [Layer 2] reasoning    — Analyse requirements and build content strategy
  [Layer 2] generator    — Generate the actual content
  [Layer 3] audit        — Log the content generation for compliance
"""
from __future__ import annotations
from orchestration.pipeline import UseCaseConfig, StepDef


def _router_input(ctx, inp):   return inp, {}
def _intent_input(ctx, inp):   return inp, {}

def _reasoning_input(ctx, inp):
    intent = ctx.get("intent", {})
    entities = intent.get("extracted_entities", {})
    return f"Analyse content requirements for: {inp}\nEntities: {entities}", {}

def _generator_input(ctx, inp):
    reasoning = ctx.get("reasoning", {})
    return inp, {"working_memory": {
        "content_strategy": (reasoning.get("conclusion") or {}).get("conclusion", ""),
        "incident_summary": inp,
    }}

def _audit_input(ctx, inp):
    all_events = []
    for s in ctx.values():
        if isinstance(s, dict):
            all_events.extend(s.get("audit_events", []))
    return all_events, {}  # passed as first positional arg (all_audit_events)


CONTENT_GENERATION_CONFIG = UseCaseConfig(
    name="Content Generation",
    description="4-agent content generation pipeline — shows the pipeline works across use cases.",
    langfuse_tags=["content-generation", "v4"],
    global_config={"max_retries": 2},
    steps=[
        StepDef(id="router",    agent="router",    label="Router Analysis",       layer=0, input_fn=_router_input),
        StepDef(id="intent",    agent="intent",    label="Intent Classification", layer=1, input_fn=_intent_input,    ),
        StepDef(id="reasoning", agent="reasoning", label="Content Strategy",      layer=2, input_fn=_reasoning_input),
        StepDef(id="generator", agent="generator", label="Content Generation",    layer=2, input_fn=_generator_input),
        StepDef(id="audit",     agent="audit",     label="Compliance Audit",      layer=3, input_fn=_audit_input,     optional=True),
    ],
)
