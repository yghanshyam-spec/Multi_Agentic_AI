"""
orchestration/use_cases/uc4_customer_support_desk.py
======================================================
Use Case 4 — AI-Powered Multilingual Customer Support Desk

Business Context:
  A B2B SaaS customer writes in Tamil about an SSO configuration problem.
  The system: detects language, classifies intent, searches the knowledge base
  via RAG, fetches live order/account status via MCP tool invocation, reasons
  on whether to auto-resolve or escalate, generates a long-form troubleshooting
  guide, translates the reply back to Tamil, and dispatches via the customer's
  preferred channel. Complex issues route through a human support agent via HITL.

Agents Used (10/21):
  router           → classify inbound ticket; dispatch to support track
  intent           → identify issue type + urgency + affected product area
  translation      → detect Tamil input; translate to English for processing;
                     translate resolution back to Tamil for delivery
  vector_query     → RAG over product documentation + known issue KB
  mcp_invoker      → call live order-status / account-status MCP tool
  reasoning        → decide: auto-resolve vs escalate; diagnose root cause
  generator        → produce step-by-step troubleshooting guide
  hitl             → human agent review for critical/complex escalations
  communication    → omnichannel dispatch (chat/email/API callback)
  audit            → customer interaction + PII compliance trail

Pipeline Layers:
  Layer 0: router
  Layer 1: intent, translation (EN)
  Layer 2: vector_query, mcp_invoker
  Layer 2: reasoning → generator
  Layer 3: hitl (conditional), translation (target lang), communication, audit
"""
from __future__ import annotations
from orchestration.pipeline import UseCaseConfig, StepDef

USE_CASE_PROMPT = (
    "Inbound customer support ticket (Tamil language):\n"
    "  'எங்கள் நிறுவனத்தின் SSO கட்டமைப்பு செயல்படவில்லை. "
    "எங்கள் Okta இணைப்பு திடீரென்று உடைந்துவிட்டது மற்றும் "
    "500 பயனர்கள் உள்நுழைய முடியவில்லை. இது மிகவும் அவசரமானது!'\n"
    "(Translation: Our company's SSO configuration is not working. "
    "Our Okta integration suddenly broke and 500 users cannot log in. "
    "This is very urgent!)\n\n"
    "Customer: TechCorp India Ltd, Plan: Enterprise, Account ID: ACC-10492\n"
    "Ticket ID: TKT-2025-08821, Channel: Chat\n\n"
    "Please:\n"
    "  1. Detect language and translate to English for processing\n"
    "  2. Classify intent and urgency\n"
    "  3. Search the SSO troubleshooting knowledge base\n"
    "  4. Check live account/subscription status via MCP tool\n"
    "  5. Reason on whether to auto-resolve or escalate to L2 support\n"
    "  6. Generate a step-by-step SSO troubleshooting guide\n"
    "  7. Escalate to human agent if critical\n"
    "  8. Translate resolution back to Tamil\n"
    "  9. Dispatch via customer's chat channel\n"
    " 10. Log full interaction for compliance"
)


# ── Input functions ──────────────────────────────────────────────────────────

def _router_input(ctx, inp):
    return inp, {}


def _translate_inbound_input(ctx, inp):
    return (
        "எங்கள் நிறுவனத்தின் SSO கட்டமைப்பு செயல்படவில்லை. "
        "எங்கள் Okta இணைப்பு திடீரென்று உடைந்துவிட்டது மற்றும் "
        "500 பயனர்கள் உள்நுழைய முடியவில்லை. இது மிகவும் அவசரமானது!",
        {
            "target_language": "en",
            "source_language": "ta",
            "domain": "technical_support",
            "target_locale": "en-GB",
        },
    )


def _intent_input(ctx, inp):
    trans = ctx.get("translation_inbound", {})
    english_text = trans.get("final_translated_text", "SSO Okta integration broken, 500 users locked out. Urgent.")
    return english_text, {}


def _vector_query_input(ctx, inp):
    intent = ctx.get("intent", {})
    return (
        "How do I fix Okta SSO SAML configuration errors? "
        "What causes sudden SSO authentication failures for enterprise customers? "
        "Steps to restore Okta integration when users are locked out.",
        {
            "agent_config": {
                "vector_store": {"table": "product_docs", "type": "pgvector"},
                "top_k": 5,
                "filters": {"min_score": 0.65},
            }
        },
    )


def _mcp_input(ctx, inp):
    return (
        "Check live account status, subscription tier, SSO configuration health, "
        "and recent auth error logs for account ID ACC-10492 (TechCorp India Ltd).",
        {
            "agent_config": {
                "mcp": {
                    "servers": [
                        {"server_id": "account_status", "url": "http://mcp-account-service:3001"},
                        {"server_id": "auth_logs", "url": "http://mcp-auth-logs:3002"},
                    ]
                }
            }
        },
    )


def _reasoning_input(ctx, inp):
    vq     = ctx.get("vector_query", {})
    mcp    = ctx.get("mcp_invoker", {})
    intent = ctx.get("intent", {})
    return (
        "Evaluate this customer support case:\n"
        "  Issue: Okta SSO integration failure — 500 enterprise users locked out\n"
        "  Urgency: CRITICAL (Enterprise plan, 500 users affected)\n"
        f"  KB findings: {vq.get('generated_answer', 'SSO troubleshooting steps retrieved')}\n"
        f"  Live account data: {mcp.get('tool_output', 'Account ACC-10492: Enterprise, SSO enabled, cert expired 2025-03-10')}\n"
        "Questions:\n"
        "  1. What is the most likely root cause of the SSO failure?\n"
        "  2. Can this be resolved with documented self-service steps?\n"
        "  3. Does the severity (500 users, Enterprise SLA) require L2 human escalation?\n"
        "  4. What is the recommended remediation sequence?",
        {},
    )


def _generator_input(ctx, inp):
    reasoning = ctx.get("reasoning", {})
    vq        = ctx.get("vector_query", {})
    mcp       = ctx.get("mcp_invoker", {})
    return (
        "Generate step-by-step Okta SSO troubleshooting and resolution guide for TechCorp India",
        {
            "working_memory": {
                "report_type": "Technical Troubleshooting Guide",
                "audience": "Enterprise IT Administrator",
                "root_cause": (reasoning.get("conclusion") or {}).get("conclusion", "Expired SAML certificate"),
                "kb_content": vq.get("generated_answer", ""),
                "account_status": mcp.get("tool_output", ""),
                "sections": [
                    "Issue Summary & Root Cause",
                    "Immediate Actions (Restore Access)",
                    "Step-by-Step Okta Reconfiguration",
                    "Verification Steps",
                    "Prevention Recommendations",
                    "Support Contacts & Escalation Path",
                ],
                "incident_summary": inp,
            }
        },
    )


def _hitl_input(ctx, inp):
    reasoning = ctx.get("reasoning", {})
    conclusion = (reasoning.get("conclusion") or {}).get("conclusion", "")
    confidence = (reasoning.get("conclusion") or {}).get("confidence", 0.7)
    return (
        "L2 Support Agent review: Critical SSO outage for Enterprise customer TechCorp India — 500 users affected",
        {
            "working_memory": {
                "risk": "high",
                "execution_plan": {
                    "script": "Manual L2 intervention: review SAML cert + Okta config for ACC-10492",
                    "target": "customer_sso_configuration",
                    "expected_outcome": "SSO restored within 30 min SLA",
                },
                "reasoning_conclusion": conclusion,
                "reasoning_confidence": confidence,
                "sla_risk": "Enterprise 99.9% SLA — breach imminent if not resolved in <20 min",
            }
        },
    )


def _translate_outbound_input(ctx, inp):
    gen   = ctx.get("generator", {})
    hitl  = ctx.get("hitl", {})
    guide = gen.get("final_document", gen.get("agent_response", {}).get("payload", {}).get("document", "Troubleshooting guide generated"))
    agent_note = f"\nL2 Support Agent is also reviewing your case: {hitl.get('decision_value','ESCALATED')}" if hitl else ""
    return (
        str(guide)[:2000] + agent_note,
        {
            "target_language": "ta",
            "source_language": "en",
            "domain": "technical_support",
            "target_locale": "ta-IN",
        },
    )


def _communication_input(ctx, inp):
    trans_out  = ctx.get("translation_outbound", {})
    gen        = ctx.get("generator", {})
    reply_text = trans_out.get("final_translated_text", "Resolution provided in Tamil")
    return (
        "Dispatch support resolution to customer TechCorp India via chat",
        {
            "channel": "chat",
            "working_memory": {
                "ticket_id": "TKT-2025-08821",
                "account_id": "ACC-10492",
                "customer": "TechCorp India Ltd",
                "resolution_tamil": str(reply_text)[:500],
                "resolution_english": str(gen.get("final_document", ""))[:300],
                "incident_summary": "SSO restoration guide delivered",
            },
        },
    )


def _audit_input(ctx, inp):
    events = []
    for s in ctx.values():
        if isinstance(s, dict):
            events.extend(s.get("audit_events", []))
    return events, {}


# ── Config ───────────────────────────────────────────────────────────────────

UC4_CUSTOMER_SUPPORT_CONFIG = UseCaseConfig(
    name="AI-Powered Multilingual Customer Support Desk",
    description=(
        "Multilingual B2B support pipeline: Tamil→EN translation, intent classification, "
        "RAG over product KB, live account status via MCP, reasoning-based escalation decision, "
        "troubleshooting guide generation, L2 HITL for critical cases, EN→Tamil reply translation, "
        "omnichannel dispatch, and PII-compliant audit trail."
    ),
    langfuse_tags=["customer-support", "multilingual", "rag", "mcp", "translation", "uc4"],
    global_config={
        "environment": "production",
        "org_name": "Acme SaaS Support",
        "sla_tier": "enterprise",
    },
    steps=[
        StepDef(id="router",              agent="router",      label="Support Ticket Router",                 layer=0, input_fn=_router_input),
        StepDef(id="translation_inbound", agent="translation", label="Inbound Language Detection & Translation (Tamil→EN)", layer=1, input_fn=_translate_inbound_input),
        StepDef(id="intent",              agent="intent",      label="Intent Classification & Urgency Detection", layer=1, input_fn=_intent_input,          ),
        StepDef(id="vector_query",        agent="vector_query", label="Knowledge Base RAG Search",            layer=2, input_fn=_vector_query_input,       ),
        StepDef(id="mcp_invoker",         agent="mcp_invoker", label="Live Account Status via MCP",           layer=2, input_fn=_mcp_input,                ),
        StepDef(id="reasoning",           agent="reasoning",   label="Root Cause & Escalation Decision",      layer=2, input_fn=_reasoning_input,          ),
        StepDef(id="generator",           agent="generator",   label="Troubleshooting Guide Generation",      layer=2, input_fn=_generator_input,          ),
        StepDef(id="hitl",                agent="hitl",        label="L2 Support Agent Review (Critical Escalation)", layer=3, input_fn=_hitl_input,      ),
        StepDef(id="translation_outbound",agent="translation", label="Resolution Translation (EN→Tamil)",     layer=3, input_fn=_translate_outbound_input),
        StepDef(id="communication",       agent="communication", label="Omnichannel Response Dispatch",      layer=3, input_fn=_communication_input,      ),
        StepDef(id="audit",               agent="audit",       label="Customer Interaction Compliance Audit", layer=3, input_fn=_audit_input,              optional=True),
    ],
)
