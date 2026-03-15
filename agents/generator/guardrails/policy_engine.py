"""agents/generator/guardrails/policy_engine.py — content safety policies for Generator."""
from shared.guardrails.base_guardrail import BaseGuardrail

class GeneratorGuardrail(BaseGuardrail):
    AGENT = "generator"
