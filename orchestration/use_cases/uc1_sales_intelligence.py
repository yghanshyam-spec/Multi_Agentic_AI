"""
orchestration/use_cases/uc1_sales_intelligence.py
===================================================
Use Case 1 — Multilingual Sales Intelligence Report

Business Context:
  A regional sales director asks for a consolidated APAC pipeline health report
  that combines live Salesforce opportunity data, internal SQL revenue metrics,
  and 3rd-party market data — translated into Mandarin and delivered by email.

Agents Used (9/21):
  router          → entry point; dispatches to specialist agents
  intent          → parse compound request into: CRM query + SQL report + translate
  salesforce      → pull live opportunity pipeline from Salesforce CRM
  sql_agent       → query internal revenue & quota-attainment data from analytics DB
  api_query       → fetch live market benchmarks from external data API
  generator       → synthesise all data sources into executive report
  translation     → translate final report from English → Mandarin (zh-CN)
  communication   → deliver translated report via email to stakeholders
  audit           → log all data access events for compliance

Pipeline Layers:
  Layer 0: router
  Layer 1: intent → salesforce, sql_agent, api_query (parallel-safe)
  Layer 2: generator → translation
  Layer 3: communication, audit
"""
from __future__ import annotations
from orchestration.pipeline import UseCaseConfig, StepDef

USE_CASE_PROMPT = (
    "Generate a comprehensive APAC Sales Intelligence Report for Q1 2025.\n"
    "Include:\n"
    "  1. Current pipeline health — all open opportunities in APAC by stage and value\n"
    "  2. Revenue attainment vs quota from the analytics database\n"
    "  3. Market benchmark comparison from external data sources\n"
    "  4. Executive summary with recommended actions\n"
    "Translate the final report into Mandarin (zh-CN) and deliver via email "
    "to the APAC Regional Sales Director and CFO."
)


# ── Input functions ─────────────────────────────────────────────────────────

def _router_input(ctx, inp):
    return inp, {}


def _intent_input(ctx, inp):
    return inp, {}


def _salesforce_input(ctx, inp):
    intent = ctx.get("intent", {})
    return (
        "Query all open APAC Opportunity records: Stage, Amount, CloseDate, AccountName, "
        "OwnerId. Filter: Region__c = 'APAC', IsClosed = false. "
        "Include total pipeline value and stage distribution summary.",
        {
            "agent_config": {
                "salesforce": {"org": "production"},
                "prompts": {
                    "parse_intent": (
                        "Parse this Salesforce request. Extract: operation_type=query, "
                        "object_type=Opportunity, filters={{Region__c:'APAC',IsClosed:false}}, "
                        "fields_needed=[Id,Name,StageName,Amount,CloseDate,AccountName]. "
                        "Return JSON."
                    )
                },
            }
        },
    )


def _sql_input(ctx, inp):
    return (
        "Show Q1 2025 revenue attainment vs quota by APAC sales rep. "
        "Include: rep_name, quota_usd, actual_revenue_usd, attainment_pct, "
        "pipeline_coverage_ratio. Sort by attainment_pct descending.",
        {},
    )


def _api_input(ctx, inp):
    return (
        "Fetch B2B SaaS market benchmarks for APAC Q1 2025: "
        "average deal size, win rate, sales cycle length, pipeline coverage ratio. "
        "Source: market intelligence API.",
        {
            "agent_config": {
                "api": {
                    "spec_url": "https://api.marketdata.example.com/openapi.json",
                    "auth": {"type": "api_key", "key": "mk_live_xxx"},
                },
                "expected_type": "market_benchmarks",
            }
        },
    )


def _generator_input(ctx, inp):
    sf   = ctx.get("salesforce", {})
    sql  = ctx.get("sql", {})
    api  = ctx.get("api_query", {})
    return (
        "Generate executive APAC Sales Intelligence Report for Q1 2025",
        {
            "working_memory": {
                "report_type": "APAC Sales Intelligence Q1 2025",
                "audience": "Regional Sales Director and CFO",
                "pipeline_data": sf.get("sf_formatted_response", "APAC pipeline data retrieved"),
                "revenue_attainment": sql.get("formatted_output", "Revenue attainment data retrieved"),
                "market_benchmarks": api.get("parsed_response", {}),
                "sections": [
                    "Executive Summary",
                    "Pipeline Health by Stage",
                    "Revenue Attainment vs Quota",
                    "Market Benchmark Comparison",
                    "Risk Analysis & Deals at Risk",
                    "Recommended Actions",
                ],
                "incident_summary": inp,
            }
        },
    )


def _translation_input(ctx, inp):
    gen = ctx.get("generator", {})
    report_text = gen.get("final_document", gen.get("agent_response", {}).get("payload", {}).get("document", "Report content"))
    return (
        str(report_text)[:3000] if report_text else "APAC Sales Intelligence Report",
        {
            "target_language": "zh-CN",
            "source_language": "en",
            "domain": "sales",
            "target_locale": "zh-CN",
        },
    )


def _communication_input(ctx, inp):
    gen        = ctx.get("generator", {})
    translation = ctx.get("translation", {})
    report_en  = gen.get("final_document", "Report generated")
    report_zh  = translation.get("final_translated_text", "报告已生成")
    return (
        "Deliver APAC Sales Intelligence Report to stakeholders",
        {
            "channel": "email",
            "working_memory": {
                "recipients": ["apac_sales_director@company.com", "cfo@company.com"],
                "subject": "APAC Sales Intelligence Report — Q1 2025",
                "english_report": str(report_en)[:500],
                "mandarin_report": str(report_zh)[:500],
                "incident_summary": "APAC Q1 Sales Intelligence Report delivery",
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

UC1_SALES_INTELLIGENCE_CONFIG = UseCaseConfig(
    name="Multilingual Sales Intelligence Report",
    description=(
        "Combines Salesforce CRM data, internal SQL analytics, and external market benchmarks "
        "into a bilingual executive report (EN + Mandarin), delivered via email with full audit trail."
    ),
    langfuse_tags=["sales-intelligence", "crm", "translation", "multilingual", "uc1"],
    global_config={
        "environment": "production",
        "org_name": "Acme Global Ltd",
        "report_locale": "zh-CN",
    },
    steps=[
        StepDef(id="router",      agent="router",      label="Entry Router — Request Dispatch",       layer=0, input_fn=_router_input),
        StepDef(id="intent",      agent="intent",      label="Intent Classification & Entity Extraction", layer=1, input_fn=_intent_input,     ),
        StepDef(id="salesforce",  agent="salesforce",  label="Salesforce APAC Pipeline Pull",         layer=1, input_fn=_salesforce_input,  ),
        StepDef(id="sql",   agent="sql",   label="Revenue Attainment SQL Query",          layer=1, input_fn=_sql_input,          ),
        StepDef(id="api_query",   agent="api_query",   label="External Market Benchmark API",         layer=1, input_fn=_api_input,          ),
        StepDef(id="generator",   agent="generator",   label="Executive Report Generation",           layer=2, input_fn=_generator_input,    ),
        StepDef(id="translation", agent="translation", label="Mandarin Translation (zh-CN)",          layer=2, input_fn=_translation_input,  ),
        StepDef(id="communication", agent="communication", label="Email Delivery to Stakeholders",    layer=3, input_fn=_communication_input),
        StepDef(id="audit",       agent="audit",       label="Data Access Compliance Audit",          layer=3, input_fn=_audit_input,         optional=True),
    ],
)
