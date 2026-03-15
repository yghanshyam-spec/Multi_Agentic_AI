"""
orchestration/use_cases/uc5_market_research_proposal.py
=========================================================
Use Case 5 — Automated Market Research & Personalised Proposal Generation

Business Context:
  A sales team closes a discovery call with a Japanese financial services firm
  (prospect: Nomura Capital Partners). The team needs a market-research-backed,
  personalised proposal — in Japanese — within 4 hours of the call. The pipeline:
  parses the brief, decomposes research into parallel tracks, ingests the
  prospect's RFP PDF, searches internal deal history, fetches live market data
  via API and MCP web search, pulls the Salesforce account profile, synthesises
  findings via reasoning, generates a bilingual proposal, translates to Japanese,
  schedules the follow-up demo, notifies the team, and logs everything.

Agents Used (16/21) — completing coverage of ALL 21 unique agents:
  intent           → parse research brief + identify prospect requirements
  planner          → decompose research into 5 parallel tracks with dependencies
  workflow         → orchestrate the full parallel research pipeline
  pdf_ingestor     → ingest prospect RFP PDF + analyst report PDFs
  vector_query     → semantic search over ingested RFP and research docs
  sql_agent        → pull internal win/loss history for finserv vertical
  api_query        → fetch live finserv market benchmarks from external API
  mcp_invoker      → invoke web search MCP for recent Nomura news + competitor intel
  salesforce       → pull account profile, past interactions, existing products
  reasoning        → synthesise all 5 research tracks → strategic insights
  generator        → generate full bilingual proposal document
  translation      → translate proposal EN → Japanese (ja-JP)
  communication    → send proposal to prospect and internal stakeholders
  scheduling_agent → book follow-up demo meeting with Nomura team
  notification_agent → alert sales team: proposal sent + demo booked
  workflow         → orchestrate and sequence all research + generation steps
  audit            → data access + IP compliance trail

Note: router, hitl, execution, sap_agent, email_handler are exercised in UC1-UC3.
      This UC intentionally uses the remaining 16 agents to complete full coverage.
"""
from __future__ import annotations
from orchestration.pipeline import UseCaseConfig, StepDef

USE_CASE_PROMPT = (
    "Prepare a market-research-backed, personalised proposal for prospect: "
    "Nomura Capital Partners (Japan), following a 60-minute discovery call.\n\n"
    "Prospect requirements identified:\n"
    "  - Agentic AI platform for trade execution automation\n"
    "  - Must support Japanese language interfaces\n"
    "  - Data residency: Japan (JP-EAST region)\n"
    "  - Compliance: FSA (Japan), MiFID II\n"
    "  - Integration: existing SAP FI + Bloomberg terminals\n"
    "  - Timeline: pilot in 90 days, full rollout in 12 months\n"
    "  - Budget indication: ¥200M–¥350M first year\n\n"
    "Research tracks required:\n"
    "  1. Ingest Nomura's RFP document (PDF) and extract requirements\n"
    "  2. Pull internal win/loss data for Japan FSA-regulated clients from analytics DB\n"
    "  3. Fetch live finserv AI market benchmarks (adoption, deal sizes, ROI stats)\n"
    "  4. Search web for recent Nomura Capital news and competitor positioning\n"
    "  5. Pull Nomura account profile from Salesforce (past touchpoints, products)\n\n"
    "Deliverables:\n"
    "  - Full proposal document (EN + Japanese translation)\n"
    "  - Book follow-up product demo with Nomura team (Teams, this Friday 10AM JST)\n"
    "  - Notify sales team and pre-sales engineer: proposal sent + demo booked\n"
    "  - Log full data access audit trail"
)


# ── Input functions ──────────────────────────────────────────────────────────

def _intent_input(ctx, inp):
    return inp, {}


def _planner_input(ctx, inp):
    intent = ctx.get("intent", {})
    return (
        "Decompose proposal preparation for Nomura Capital Partners into parallel research tracks:\n"
        "  Track A: Ingest RFP PDF → RAG search for requirements\n"
        "  Track B: SQL query → internal finserv win/loss history\n"
        "  Track C: API query → live market benchmarks\n"
        "  Track D: MCP web search → Nomura news + competitor intel\n"
        "  Track E: Salesforce pull → account profile + past touchpoints\n"
        "  Track F (sequential): Reasoning → synthesise all tracks\n"
        "  Track G (sequential): Generator → produce proposal\n"
        "  Track H (sequential): Translation → Japanese\n"
        "Return a dependency-aware task graph in JSON.",
        {},
    )


def _pdf_input(ctx, inp):
    return (
        "Ingest Nomura Capital Partners RFP document and FinServ AI analyst report into document store",
        {
            "pdf_path": "nomura_rfp_2025_q1.pdf",
            "agent_config": {
                "chunk_size": 500,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "vector_store": {"table": "prospect_docs", "type": "pgvector"},
            },
        },
    )


def _vector_query_input(ctx, inp):
    pdf = ctx.get("pdf_ingestor", {})
    return (
        "What are Nomura Capital Partners' specific requirements for AI trade execution? "
        "What compliance frameworks are mentioned? What integration specifications are listed? "
        "What are the evaluation criteria and scoring weights?",
        {
            "agent_config": {
                "vector_store": {"table": "prospect_docs", "type": "pgvector"},
                "top_k": 6,
                "filters": {"min_score": 0.6},
            }
        },
    )


def _sql_input(ctx, inp):
    return (
        "Show win/loss analysis for Japanese and FSA-regulated financial services clients "
        "in the last 24 months. Include: client_name, deal_value_usd, outcome, "
        "product_sold, sales_cycle_days, key_win_factors, loss_reasons. "
        "Also show average deal size and win rate for finserv vertical in APAC.",
        {},
    )


def _api_input(ctx, inp):
    return (
        "Fetch finserv AI adoption benchmarks for Japan and APAC 2024-2025: "
        "AI investment growth rate, trade automation adoption %, average ROI from AI platforms, "
        "typical implementation timelines, regulatory readiness scores (FSA, MAS).",
        {
            "agent_config": {
                "api": {
                    "spec_url": "https://api.fintechresearch.example.com/openapi.json",
                    "auth": {"type": "api_key", "key": "ftr_live_xxx"},
                },
                "expected_type": "market_benchmarks",
            }
        },
    )


def _mcp_input(ctx, inp):
    return (
        "Search for: (1) Recent news about Nomura Capital Partners AI strategy and technology investments, "
        "(2) Competitor positioning for AI trade execution platforms in Japan (Bloomberg, Refinitiv, Palantir), "
        "(3) FSA Japan AI regulatory guidance 2024-2025.",
        {
            "agent_config": {
                "mcp": {
                    "servers": [
                        {"server_id": "web_search", "url": "stdio://mcp-web-search"},
                    ]
                }
            }
        },
    )


def _salesforce_input(ctx, inp):
    return (
        "Pull Nomura Capital Partners Salesforce account profile: account history, "
        "all past opportunities and their outcomes, current products in use, "
        "key contacts, last 6 months activity log, and any existing relationship notes.",
        {
            "agent_config": {
                "salesforce": {"org": "production"},
            }
        },
    )


def _reasoning_input(ctx, inp):
    vq   = ctx.get("vector_query", {})
    sql  = ctx.get("sql", {})
    api  = ctx.get("api_query", {})
    mcp  = ctx.get("mcp_invoker", {})
    sf   = ctx.get("salesforce", {})
    return (
        "Synthesise all research tracks into strategic proposal insights for Nomura Capital Partners:\n\n"
        f"RFP Requirements (from PDF): {vq.get('generated_answer', 'Requirements extracted')}\n\n"
        f"Internal Win/Loss History: {sql.get('formatted_output', 'Finserv win rate: 68%')}\n\n"
        f"Market Benchmarks: {api.get('parsed_response', 'Japan finserv AI adoption: 34% YoY growth')}\n\n"
        f"Nomura News & Competitor Intel: {mcp.get('tool_output', 'Nomura invested ¥15B in AI infra 2024')}\n\n"
        f"Salesforce Account Profile: {sf.get('sf_formatted_response', '2 past opportunities, warm relationship')}\n\n"
        "Strategic questions to address:\n"
        "  1. How do our capabilities map to Nomura's stated requirements?\n"
        "  2. What are our 3 strongest differentiators vs competitors in this deal?\n"
        "  3. What objections are likely and how should we pre-empt them?\n"
        "  4. What deal structure (pricing, timeline, pilot scope) maximises win probability?\n"
        "  5. What risks exist (regulatory, technical, political) and how do we mitigate?\n"
        "  6. What is the recommended proposal narrative arc?",
        {},
    )


def _generator_input(ctx, inp):
    reasoning = ctx.get("reasoning", {})
    vq        = ctx.get("vector_query", {})
    sf        = ctx.get("salesforce", {})
    return (
        "Generate comprehensive proposal document for Nomura Capital Partners — Agentic AI Platform",
        {
            "working_memory": {
                "report_type": "Sales Proposal",
                "audience": "Nomura Capital Partners CTO and Procurement Committee",
                "prospect": "Nomura Capital Partners, Japan",
                "strategic_insights": (reasoning.get("conclusion") or {}).get("conclusion", ""),
                "rfp_requirements": vq.get("generated_answer", ""),
                "account_history": sf.get("sf_formatted_response", ""),
                "sections": [
                    "Executive Summary",
                    "Understanding Your Requirements",
                    "Our Solution Architecture for Trade Execution AI",
                    "FSA & MiFID II Compliance Framework",
                    "Japanese Language & Data Residency Capabilities",
                    "SAP FI + Bloomberg Integration Approach",
                    "Implementation Roadmap (90-day Pilot → 12-month Rollout)",
                    "Pricing & Commercial Model (¥200M–¥350M range)",
                    "Case Studies: FSA-Regulated Clients",
                    "Why Acme AI vs Competitors",
                    "Risk Mitigation & SLA Commitments",
                    "Next Steps & Proposed Demo Agenda",
                ],
                "incident_summary": inp,
            }
        },
    )


def _translation_input(ctx, inp):
    gen = ctx.get("generator", {})
    doc = gen.get("final_document", gen.get("agent_response", {}).get("payload", {}).get("document", "Proposal generated"))
    return (
        str(doc)[:3000] if doc else "Proposal content",
        {
            "target_language": "ja",
            "source_language": "en",
            "domain": "financial_services",
            "target_locale": "ja-JP",
        },
    )


def _communication_input(ctx, inp):
    gen   = ctx.get("generator", {})
    trans = ctx.get("translation", {})
    return (
        "Send personalised proposal to Nomura Capital Partners and internal stakeholders",
        {
            "channel": "email",
            "working_memory": {
                "recipients": [
                    "cto@nomura-capital.co.jp",
                    "procurement@nomura-capital.co.jp",
                    "account_executive@company.com",
                    "presales@company.com",
                ],
                "subject": "Acme Agentic AI Platform — Proposal for Nomura Capital Partners",
                "proposal_english": str(gen.get("final_document", ""))[:400],
                "proposal_japanese": str(trans.get("final_translated_text", ""))[:400],
                "incident_summary": "Proposal delivery: Nomura Capital Partners",
            },
        },
    )


def _scheduling_input(ctx, inp):
    comm = ctx.get("communication", {})
    return (
        "Schedule a 90-minute product demo with Nomura Capital Partners team "
        "this Friday 2025-03-14 at 10:00 AM JST. "
        "Participants: CTO Yamamoto-san, our Account Executive, Pre-sales Engineer. "
        "Platform: Microsoft Teams. Include Japanese language interpreter if available.",
        {
            "agent_config": {
                "calendar": {"platform": "teams"},
            }
        },
    )


def _notification_input(ctx, inp):
    comm  = ctx.get("communication", {})
    sched = ctx.get("scheduling", {})
    return (
        "Internal alert: Nomura proposal sent and demo booked",
        {
            "event_payload": {
                "type": "PROPOSAL_DELIVERED",
                "source": "market_research_proposal_workflow",
                "severity": "low",
                "details": (
                    "Proposal delivered to Nomura Capital Partners. "
                    f"Demo booked: {sched.get('scheduling_summary', 'Friday 10AM JST via Teams')}. "
                    "Deal value: ¥200M–¥350M. Next action: demo prep by Thursday."
                ),
                "recipients": ["account_executive@company.com", "presales@company.com", "sales_manager@company.com"],
                "prospect": "Nomura Capital Partners",
                "deal_value": "¥200M–¥350M",
            }
        },
    )


def _workflow_input(ctx, inp):
    planner = ctx.get("planner", {})
    return (
        "Orchestrate and verify all research + proposal generation tracks for Nomura Capital proposal",
        {"workflow_plan": planner.get("workflow_plan")},
    )


def _audit_input(ctx, inp):
    events = []
    for s in ctx.values():
        if isinstance(s, dict):
            events.extend(s.get("audit_events", []))
    return events, {}


# ── Config ───────────────────────────────────────────────────────────────────

UC5_MARKET_RESEARCH_PROPOSAL_CONFIG = UseCaseConfig(
    name="Automated Market Research & Personalised Proposal Generation",
    description=(
        "Full-cycle proposal pipeline: intent parsing → research decomposition (Planner) → "
        "5 parallel research tracks (PDF RAG, SQL, external API, MCP web search, Salesforce) → "
        "reasoning-based synthesis → bilingual proposal generation (EN + Japanese) → "
        "email delivery → demo scheduling → internal notification → compliance audit. "
        "Covers 16 agents, completing all-21 coverage across the 5 use cases."
    ),
    langfuse_tags=["market-research", "proposal", "finserv", "japanese", "multilingual", "uc5"],
    global_config={
        "environment": "production",
        "org_name": "Acme Global AI",
        "prospect_region": "Japan",
    },
    steps=[
        StepDef(id="intent",             agent="intent",            label="Research Brief Intent Parsing",              layer=1, input_fn=_intent_input),
        StepDef(id="planner",            agent="planner",           label="Research Track Decomposition",               layer=0, input_fn=_planner_input,      ),
        # ── Parallel research tracks (all depend on planner) ──
        StepDef(id="pdf_ingestor",       agent="pdf_ingestor",      label="RFP & Analyst Report PDF Ingestion",         layer=1, input_fn=_pdf_input,           ),
        StepDef(id="sql",          agent="sql",         label="Internal FinServ Win/Loss SQL Query",        layer=1, input_fn=_sql_input,           ),
        StepDef(id="api_query",          agent="api_query",         label="Live Market Benchmark API",                  layer=1, input_fn=_api_input,           ),
        StepDef(id="mcp_invoker",        agent="mcp_invoker",       label="Competitor & News Web Search (MCP)",         layer=1, input_fn=_mcp_input,           ),
        StepDef(id="salesforce",         agent="salesforce",        label="Salesforce Account Profile Pull",            layer=1, input_fn=_salesforce_input,    ),
        # ── RAG over ingested RFP ──
        StepDef(id="vector_query",       agent="vector_query",      label="RFP Requirements RAG Search",                layer=2, input_fn=_vector_query_input,  ),
        # ── Synthesis ──
        StepDef(id="reasoning",          agent="reasoning",         label="Strategic Insights Synthesis",               layer=2, input_fn=_reasoning_input,     ),
        # ── Generation ──
        StepDef(id="generator",          agent="generator",         label="Bilingual Proposal Generation",              layer=2, input_fn=_generator_input,     ),
        StepDef(id="translation",        agent="translation",       label="Japanese Translation (ja-JP)",               layer=3, input_fn=_translation_input,   ),
        # ── Delivery ──
        StepDef(id="communication",      agent="communication",     label="Proposal Email Delivery",                    layer=3, input_fn=_communication_input),
        StepDef(id="scheduling",   agent="scheduling",  label="Follow-Up Demo Scheduling",                  layer=3, input_fn=_scheduling_input,   ),
        StepDef(id="notification", agent="notification", label="Internal Sales Team Alert",                layer=3, input_fn=_notification_input),
        StepDef(id="workflow",           agent="workflow",          label="Research Pipeline Orchestration",            layer=1, input_fn=_workflow_input,      ),
        StepDef(id="audit",              agent="audit",             label="Data Access & IP Compliance Audit",          layer=3, input_fn=_audit_input,          optional=True),
    ],
)
