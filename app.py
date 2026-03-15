"""
app.py
======
Streamlit UI for the Agentic AI Accelerator v4.
5 production use cases + Custom use case via AutoOrchestrator.

Run with:  streamlit run app.py
"""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from orchestration.pipeline import run_pipeline, PipelineResult, StepResult
from orchestration.auto_orchestrator import (
    run_auto, build_auto_pipeline, analyse_request, AutoPipelineResult,
)
from orchestration.use_cases.uc1_sales_intelligence         import UC1_SALES_INTELLIGENCE_CONFIG,       USE_CASE_PROMPT as PROMPT_UC1
from orchestration.use_cases.uc2_employee_onboarding        import UC2_EMPLOYEE_ONBOARDING_CONFIG,      USE_CASE_PROMPT as PROMPT_UC2
from orchestration.use_cases.uc3_procurement_exception      import UC3_PROCUREMENT_EXCEPTION_CONFIG,    USE_CASE_PROMPT as PROMPT_UC3
from orchestration.use_cases.uc4_customer_support_desk      import UC4_CUSTOMER_SUPPORT_CONFIG,         USE_CASE_PROMPT as PROMPT_UC4
from orchestration.use_cases.uc5_market_research_proposal   import UC5_MARKET_RESEARCH_PROPOSAL_CONFIG, USE_CASE_PROMPT as PROMPT_UC5
from shared import new_id

# ─────────────────────────────────────────────────────────────────────────────
# Page config & CSS
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Agentic AI Accelerator", page_icon="◉",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;background-color:#f8f9fb;color:#1a202c;}
.stApp{background-color:#f8f9fb;}.main .block-container{padding:2rem 2.5rem;max-width:1400px;}
[data-testid="stSidebar"]{background:#ffffff;border-right:1px solid #e2e8f0;}
[data-testid="stSidebar"] .block-container{padding:1.5rem 1.2rem;}
h1{font-family:'Inter',sans-serif;font-weight:700;letter-spacing:-0.5px;color:#111827;font-size:1.9rem;}
h2{font-family:'Inter',sans-serif;font-weight:600;color:#1f2937;}
h3{font-family:'Inter',sans-serif;font-weight:600;color:#374151;font-size:1.05rem;}
p,li{color:#4b5563;line-height:1.65;}
[data-testid="stMetric"]{background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;padding:16px !important;box-shadow:0 1px 3px rgba(0,0,0,0.05);}
[data-testid="stMetric"] label{color:#6b7280 !important;font-size:11px !important;letter-spacing:0.8px;text-transform:uppercase;font-weight:500 !important;}
[data-testid="stMetricValue"]{color:#1d4ed8 !important;font-family:'JetBrains Mono',monospace !important;font-size:22px !important;font-weight:500 !important;}
code,pre{font-family:'JetBrains Mono',monospace !important;font-size:13px;}
.stCodeBlock{border-radius:8px;border:1px solid #e5e7eb;}
.stButton>button{background:#e5e7eb;color:#374151;border:1px solid #d1d5db;border-radius:8px;font-family:'Inter',sans-serif;font-weight:600;font-size:14px;padding:0.55rem 1.4rem;transition:background 0.2s,color 0.2s,box-shadow 0.2s,border-color 0.2s;}
.stButton>button:hover{background:#bfdbfe;color:#1d4ed8;border-color:#93c5fd;box-shadow:0 4px 14px rgba(59,130,246,0.18);}
.stButton>button:active{background:#93c5fd;color:#1e40af;}
.streamlit-expanderHeader{background:#ffffff !important;border:1px solid #e5e7eb !important;border-radius:8px !important;font-family:'JetBrains Mono',monospace !important;font-size:12px !important;color:#374151 !important;}
.stTabs [data-baseweb="tab-list"]{background:#ffffff;border-radius:10px 10px 0 0;border-bottom:1px solid #e5e7eb;}
.stTabs [data-baseweb="tab"]{font-family:'Inter',sans-serif;font-size:13px;font-weight:500;color:#6b7280;}
.stTabs [aria-selected="true"]{color:#1d4ed8 !important;}
.stTextArea>div>div>textarea{background:#ffffff !important;border:1px solid #d1d5db !important;border-radius:8px !important;font-family:'Inter',sans-serif !important;font-size:14px !important;color:#1f2937 !important;}
hr{border-color:#e5e7eb;}.stAlert{border-radius:8px;}
.sidebar-label{font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;font-weight:600;margin-top:10px;}
.agent-msg-card{background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;padding:12px 16px;margin:6px 0;}
.flow-arrow{text-align:center;color:#93c5fd;font-size:18px;margin:2px 0;}
</style>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# USE CASE CATALOGUE
# ─────────────────────────────────────────────────────────────────────────────
USE_CASES = [
    {"key":"uc1_sales_intelligence","label":"UC1 · Multilingual Sales Intelligence Report  (9 agents)",
     "short":"UC1 — Sales Intelligence","agent_count":9,"config":UC1_SALES_INTELLIGENCE_CONFIG,"prompt":PROMPT_UC1,
     "badge_color":"#1d4ed8","description":"APAC pipeline health · Salesforce + SQL + Market API · Mandarin translation · Email delivery",
     "agents":["router","intent","salesforce","sql","api_query","generator","translation","communication","audit"]},
    {"key":"uc2_employee_onboarding","label":"UC2 · End-to-End Employee Onboarding  (10 agents)",
     "short":"UC2 — Employee Onboarding","agent_count":10,"config":UC2_EMPLOYEE_ONBOARDING_CONFIG,"prompt":PROMPT_UC2,
     "badge_color":"#7c3aed","description":"SAP HR record · PDF policy RAG · Account provisioning · Teams scheduling · Notifications",
     "agents":["planner","workflow","pdf_ingestor","vector_query","sap","email_handler","scheduling","hitl","execution","notification"]},
    {"key":"uc3_procurement_exception","label":"UC3 · Procurement Exception & Vendor Dispute  (9 agents)",
     "short":"UC3 — Procurement Exception","agent_count":9,"config":UC3_PROCUREMENT_EXCEPTION_CONFIG,"prompt":PROMPT_UC3,
     "badge_color":"#059669","description":"Vendor dispute email · SAP PO/GR pull · Evidence reasoning · HITL approval · SOX audit",
     "agents":["router","email_handler","sap","reasoning","hitl","execution","communication","notification","audit"]},
    {"key":"uc4_customer_support","label":"UC4 · AI-Powered Multilingual Customer Support  (10 agents)",
     "short":"UC4 — Customer Support Desk","agent_count":10,"config":UC4_CUSTOMER_SUPPORT_CONFIG,"prompt":PROMPT_UC4,
     "badge_color":"#0891b2","description":"Tamil→EN translation · KB RAG · MCP live status · Escalation reasoning · HITL · Tamil reply",
     "agents":["router","translation","intent","vector_query","mcp_invoker","reasoning","generator","hitl","communication","audit"]},
    {"key":"uc5_market_research","label":"UC5 · Market Research & Personalised Proposal  (16 agents)",
     "short":"UC5 — Market Research & Proposal","agent_count":16,"config":UC5_MARKET_RESEARCH_PROPOSAL_CONFIG,"prompt":PROMPT_UC5,
     "badge_color":"#dc2626","description":"RFP ingestion · 5 parallel research tracks · Synthesis · Japanese proposal · Demo scheduling",
     "agents":["intent","planner","workflow","pdf_ingestor","vector_query","sql","api_query","mcp_invoker","salesforce","reasoning","generator","translation","communication","scheduling","notification","audit"]},
]
UC_LABELS = [uc["label"] for uc in USE_CASES]

# ─────────────────────────────────────────────────────────────────────────────
# AGENT LAYER TAXONOMY
# ─────────────────────────────────────────────────────────────────────────────
ALL_AGENT_LAYERS = {
    "router":(0,"⬡","#1d4ed8","Router"),"intent":(1,"◈","#7c3aed","Intent"),
    "planner":(1,"◉","#7c3aed","Planner"),"workflow":(1,"◎","#7c3aed","Workflow"),
    "reasoning":(2,"◆","#059669","Reasoning"),"generator":(2,"◇","#059669","Generator"),
    "communication":(2,"◌","#059669","Communication"),"translation":(2,"◐","#059669","Translation"),
    "sql":(2,"⬘","#0891b2","SQL"),"pdf_ingestor":(2,"⬙","#0891b2","PDF Ingestor"),
    "vector_query":(2,"⬚","#0891b2","Vector Query"),"api_query":(2,"⊞","#0891b2","API Query"),
    "mcp_invoker":(2,"⊟","#d97706","MCP Invoker"),"salesforce":(2,"◑","#d97706","Salesforce"),
    "sap":(2,"◒","#d97706","SAP"),"email_handler":(2,"◓","#d97706","Email Handler"),
    "execution":(3,"⚙","#0891b2","Execution"),"hitl":(3,"⚑","#dc2626","HITL"),
    "audit":(3,"◼","#dc2626","Audit"),"notification":(3,"◻","#dc2626","Notification"),
    "scheduling":(3,"◷","#dc2626","Scheduling"),
}
LAYER_NAMES  = {0:"Layer 0 — Entry",1:"Layer 1 — Orchestration",
                2:"Layer 2 — Intelligence / Data / Integration",3:"Layer 3 — Governance"}
LAYER_COLORS = {0:"#1d4ed8",1:"#7c3aed",2:"#059669",3:"#dc2626"}
STEP_DISPLAY = {k:(v[3],v[0],v[1],v[2]) for k,v in ALL_AGENT_LAYERS.items()}
STEP_DISPLAY.update({
    "router_initial":("Router",0,"⬡","#1d4ed8"),"router_final":("Router ②",0,"⬡","#1d4ed8"),
    "translation_inbound":("Translation →EN",2,"◐","#059669"),
    "translation_outbound":("Translation →TL",2,"◐","#059669"),
    "sap_agent":("SAP",2,"◒","#d97706"),"sql_agent":("SQL",2,"⬘","#0891b2"),
    "notification_agent":("Notification",3,"◻","#dc2626"),
    "scheduling_agent":("Scheduling",3,"◷","#dc2626"),
})

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _step(result, step_id):
    return next((s for s in result.steps if s.step_id == step_id), None)

def _uc_by_label(label):
    return next(uc for uc in USE_CASES if uc["label"] == label)

def _get_compliance_score(result):
    a = _step(result, "audit")
    return a.key_output.get("compliance_score", 1.0) if a else 1.0

def _get_hitl_decision(result):
    h = _step(result, "hitl")
    return str(h.key_output.get("decision", "APPROVED")) if h else "N/A"

def _get_incident_report(result):
    g = _step(result, "generator")
    return g.full_state.get("final_document", "") if g else ""

def _get_stakeholder_email(result):
    c = _step(result, "communication")
    return c.full_state.get("draft_response", "") if c else ""

def _get_execution_report(result):
    e = _step(result, "execution")
    return e.full_state.get("execution_report", "") if e else ""

def _get_audit_report(result):
    a = _step(result, "audit")
    return a.full_state.get("audit_report", {}) if a else {}

def _extract_agent_message(step: StepResult) -> str:
    """
    Extract the human-readable output from an AgentResponse envelope.
    build_agent_response() in every agent's graph.py produces:
      state["agent_response"] = {"message": ..., "payload": {...}, ...}
    Falls back through well-known state keys if envelope is absent.
    """
    state = step.full_state
    # 1. Canonical AgentResponse envelope
    ar = state.get("agent_response", {})
    if isinstance(ar, dict):
        for k in ("message", "summary"):
            v = ar.get(k)
            if v:
                return str(v)[:600]
        payload = ar.get("payload", {})
        if isinstance(payload, dict):
            for k in ("result","summary","output","document","translated_text",
                      "answer","report","response","message"):
                v = payload.get(k)
                if v:
                    return str(v)[:600]
    # 2. Fallback top-level state keys
    for k in ("final_document","conclusion","final_translated_text","draft_response",
              "generated_answer","formatted_output","audit_report","dispatch_result",
              "scheduling_summary","parsed_response","sap_summary","sf_formatted_response",
              "reply_draft","tool_output","ingestion_summary","validated_plan",
              "workflow_summary","aggregated_results","final_response"):
        v = state.get(k)
        if v:
            return str(v)[:600]
    return "(no output)"

def _render_agent_message_flow(steps):
    """Render inter-agent AgentResponse message chain."""
    for i, step in enumerate(steps):
        lc   = LAYER_COLORS.get(step.layer, "#6b7280")
        icon = ALL_AGENT_LAYERS.get(step.agent, (0,"·","#6b7280",step.agent))[1]
        ok   = step.status not in ("FAILED","CANCELLED")
        sc   = "#059669" if ok else "#dc2626"
        msg  = _extract_agent_message(step)
        st.markdown(f"""<div class="agent-msg-card" style="border-left:3px solid {lc};">
  <div style="font-size:10px;color:#6b7280;letter-spacing:0.8px;text-transform:uppercase;font-weight:600;margin-bottom:4px;">
    <span style="color:{lc};">{icon} {step.step_label}</span>
    &nbsp;·&nbsp;<span style="color:{sc};">{'✓' if ok else '✗'} {step.status}</span>
    &nbsp;·&nbsp;{step.duration_ms}ms&nbsp;·&nbsp;<span style="color:#9ca3af;">Layer {step.layer}</span>
  </div>
  <div style="font-size:13px;color:#1f2937;line-height:1.6;">{msg}</div>
</div>""", unsafe_allow_html=True)
        if i < len(steps) - 1:
            st.markdown("<div class='flow-arrow'>↓ AgentResponse</div>", unsafe_allow_html=True)

def _step_indicators(step_ids):
    n = min(len(step_ids), 11)
    pcols = st.columns(n)
    pph = {}
    for i, sid in enumerate(step_ids):
        d = STEP_DISPLAY.get(sid, (sid,0,"·","#9ca3af"))
        lbl,_,icon,color = d[0],d[1],d[2],d[3]
        with pcols[i % n]:
            ph = st.empty()
            ph.markdown(f"<div style='text-align:center;'><div style='font-size:15px;color:{color};opacity:0.25;'>{icon}</div><div style='font-size:8px;color:#9ca3af;font-family:JetBrains Mono;margin-top:1px;'>{lbl[:9]}</div></div>", unsafe_allow_html=True)
            pph[sid] = (ph, icon, color, lbl)
    return pph, st.progress(0), st.empty()

def _make_on_step(pph, pbar, ptext, n):
    done = [0]
    def on_step(sid, slabel, layer, status):
        if sid not in pph: return
        ph, icon, color, _ = pph[sid]
        if status == "running":
            ph.markdown(f"<div style='text-align:center;'><div style='font-size:15px;color:{color};'>{icon}</div><div style='font-size:8px;color:#d97706;font-family:JetBrains Mono;margin-top:1px;'>running</div></div>", unsafe_allow_html=True)
            ptext.markdown(f"<span style='font-family:JetBrains Mono;font-size:12px;color:#d97706;'>▶ {slabel}</span>", unsafe_allow_html=True)
        elif status in ("COMPLETED","completed"):
            done[0] += 1
            ph.markdown(f"<div style='text-align:center;'><div style='font-size:15px;color:{color};'>{icon}</div><div style='font-size:8px;color:#059669;font-family:JetBrains Mono;margin-top:1px;'>✓ done</div></div>", unsafe_allow_html=True)
            pbar.progress(min(done[0]/max(n,1), 1.0))
        elif status == "failed":
            ph.markdown(f"<div style='text-align:center;'><div style='font-size:15px;color:#dc2626;'>{icon}</div><div style='font-size:8px;color:#dc2626;font-family:JetBrains Mono;margin-top:1px;'>✗ fail</div></div>", unsafe_allow_html=True)
    return on_step


# ─────────────────────────────────────────────────────────────────────────────
# RESULTS RENDERER  (shared by production UCs and custom auto UC)
# ─────────────────────────────────────────────────────────────────────────────

def _render_results(result: PipelineResult, ruc: dict, show_raw: bool,
                    auto_res=None) -> None:
    compliance  = _get_compliance_score(result)
    hitl_dec    = _get_hitl_decision(result)
    inc_report  = _get_incident_report(result)
    stk_email   = _get_stakeholder_email(result)
    exec_report = _get_execution_report(result)
    audit_rpt   = _get_audit_report(result)
    failed      = [s for s in result.steps if s.status == "FAILED"]

    st.divider()
    bc = ruc.get("badge_color","#6b7280")
    st.markdown(
        f"<span style='background:{bc}18;color:{bc};border:1px solid {bc}44;"
        f"font-size:10px;font-weight:600;letter-spacing:0.8px;text-transform:uppercase;"
        f"padding:3px 10px;border-radius:20px;'>{ruc.get('short','Pipeline')}</span>"
        f"<span style='font-size:12px;color:#6b7280;margin-left:8px;'>{ruc.get('description','')}</span>",
        unsafe_allow_html=True)

    if auto_res:
        st.info(f"🤖 **Auto-Orchestrated** · {auto_res.plan.use_case_title}  "
                f"·  {len(auto_res.execution_order)} agents  "
                f"·  {auto_res.plan.reasoning}")

    st.markdown("### Pipeline Summary")
    m1,m2,m3,m4,m5,m6 = st.columns(6)
    with m1: st.metric("Duration",      f"{result.total_duration_ms:,}ms")
    with m2: st.metric("Steps Run",     len(result.steps))
    with m3: st.metric("Agents",        ruc.get("agent_count", len(result.steps)))
    with m4: st.metric("HITL Decision", hitl_dec)
    with m5: st.metric("Compliance",    f"{compliance:.0%}")
    with m6: st.metric("Audit Events",  len(result.all_audit_events))

    if failed:
        st.warning("⚠ " + str(len(failed)) + " step(s) failed: " +
                   ", ".join(s.step_label for s in failed))

    st.divider()

    t1,t2,t3,t4,t5,t6 = st.tabs([
        "🏃 Agent Flow & Messages","📄 Output Report","📧 Communication",
        "⚙ Execution","📊 Audit Trail","🔍 Raw State",
    ])

    # TAB 1 ── Agent Flow & Messages ──────────────────────────────────────────
    with t1:
        st.markdown("#### Inter-Agent Message Flow  *(via AgentResponse)*")
        st.caption("Each card shows the AgentResponse output from that agent. "
                   "↓ arrows show data direction through the pipeline.")
        _render_agent_message_flow(result.steps)

        st.markdown("---")
        st.markdown("#### Execution Detail")
        cur_layer = -1
        for step in result.steps:
            if step.layer != cur_layer:
                cur_layer = step.layer
                lc = LAYER_COLORS.get(step.layer,"#6b7280")
                st.markdown(f"<div style='background:#f0f4ff;border-left:3px solid {lc};"
                    f"padding:5px 14px;margin:14px 0 6px;font-size:11px;color:{lc};"
                    f"font-weight:600;letter-spacing:1px;text-transform:uppercase;"
                    f"border-radius:0 6px 6px 0;'>{LAYER_NAMES.get(step.layer,f'Layer {step.layer}')}</div>",
                    unsafe_allow_html=True)
            ok = step.status not in ("FAILED","CANCELLED")
            with st.expander(
                f"{'✓' if ok else '✗'} {step.step_label}  ·  {step.duration_ms}ms  ·  "
                f"{len(step.trace)} nodes  ·  {len(step.audit_events)} events", expanded=False):
                c1,c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Status:** `{step.status}`")
                    st.markdown(f"**Agent:** `{step.agent}`")
                    if step.key_output:
                        st.markdown("**Key Outputs:**")
                        for k,v in step.key_output.items():
                            if v not in (None,"",[]):
                                st.markdown(f"- `{k}`: {str(v)[:200]}")
                    ar = step.full_state.get("agent_response")
                    if ar and isinstance(ar, dict):
                        st.markdown("**AgentResponse:**")
                        st.json({k:str(v)[:200] for k,v in ar.items()})
                with c2:
                    if step.trace:
                        st.markdown("**Node Trace:**")
                        for t in step.trace:
                            dot = "🔴" if t.get("llm_tokens_used",0)>0 else "🟢"
                            st.markdown(f"<span style='font-family:JetBrains Mono;font-size:11px;color:#6b7280;'>"
                                f"{dot} {t.get('node_name','?')} &nbsp; {t.get('duration_ms',0)}ms</span>",
                                unsafe_allow_html=True)
                if step.error:
                    st.error(f"Error: {step.error}")

        st.markdown("#### ⏱ Execution Timeline")
        st.bar_chart({"Step":[s.step_label[:20] for s in result.steps],
                      "Duration (ms)":[s.duration_ms for s in result.steps]},
                     x="Step",y="Duration (ms)",height=260)

    # TAB 2 ── Output Report ──────────────────────────────────────────────────
    with t2:
        st.markdown("#### Generated Output")
        r_s = _step(result,"reasoning")
        if r_s:
            c = r_s.key_output.get("conclusion","")
            if c:
                st.markdown(f"<div style='background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:14px 18px;margin-bottom:18px;'>"
                    f"<div style='font-size:10px;color:#166534;letter-spacing:1px;text-transform:uppercase;font-weight:600;margin-bottom:5px;'>🧠 Reasoning — Conclusion</div>"
                    f"<div style='color:#14532d;font-size:14px;'>{c}</div></div>", unsafe_allow_html=True)
        for tsid in ["translation","translation_outbound","translation_inbound"]:
            ts = _step(result,tsid)
            if ts and ts.key_output.get("translated"):
                txt = ts.full_state.get("final_translated_text","")
                if txt:
                    sl = ts.key_output.get("source_lang","?")
                    tl = ts.key_output.get("target_lang","?")
                    st.markdown(f"<div style='background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:14px 18px;margin-bottom:18px;'>"
                        f"<div style='font-size:10px;color:#1d4ed8;letter-spacing:1px;text-transform:uppercase;font-weight:600;margin-bottom:5px;'>🌐 Translation {sl} → {tl}</div>"
                        f"<div style='color:#1e3a8a;font-size:13px;line-height:1.6;'>{str(txt)[:600]}</div></div>", unsafe_allow_html=True)
                    break
        if inc_report:
            st.markdown(inc_report)
        else:
            g = _step(result,"generator")
            if g:
                pay = g.full_state.get("agent_response",{})
                doc = (pay.get("payload",{}).get("document","") if isinstance(pay,dict) else "")
                st.markdown(doc) if doc else st.info("Generator ran — no structured document output.")
            else:
                st.info("No generator step in this pipeline.")

    # TAB 3 ── Communication ──────────────────────────────────────────────────
    with t3:
        st.markdown("#### Stakeholder Communication")
        cs = _step(result,"communication")
        if cs:
            c1,c2,c3 = st.columns(3)
            with c1: st.metric("Channel", cs.key_output.get("channel","email"))
            with c2: st.metric("Priority","high")
            with c3: st.metric("Status",  str(cs.key_output.get("dispatched","DISPATCHED")))
        if stk_email:
            st.markdown("---")
            st.markdown(f"<div style='background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;padding:20px;font-family:Inter,sans-serif;font-size:13px;white-space:pre-wrap;color:#1f2937;line-height:1.7;'>{stk_email}</div>", unsafe_allow_html=True)
        else:
            ns = _step(result,"notification")
            if ns:
                msg = ns.full_state.get("crafted_message","")
                ch  = ns.key_output.get("channel","")
                if msg:
                    st.markdown(f"**Notification via {ch}:**")
                    st.markdown(f"<div style='background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;padding:20px;font-family:Inter,sans-serif;font-size:13px;white-space:pre-wrap;color:#1f2937;line-height:1.7;'>{str(msg)[:800]}</div>", unsafe_allow_html=True)
                else:
                    st.info("Notification agent ran — no crafted message.")
            else:
                st.info("No communication or notification step in this pipeline.")

    # TAB 4 ── Execution ──────────────────────────────────────────────────────
    with t4:
        st.markdown("#### Execution & Scheduling")
        hs = _step(result,"hitl"); es = _step(result,"execution"); ss = _step(result,"scheduling")
        if hs:
            dec  = hs.key_output.get("decision","APPROVED")
            dc   = "#059669" if str(dec)=="APPROVED" else "#dc2626"
            st.markdown(f"<div style='background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:14px 18px;margin-bottom:16px;'>"
                f"<div style='font-size:10px;color:#991b1b;letter-spacing:1px;text-transform:uppercase;font-weight:600;'>⚑ HITL Checkpoint</div>"
                f"<div style='margin-top:8px;'><span style='font-family:JetBrains Mono;font-size:13px;color:#374151;'>"
                f"Decision: <b style='color:{dc};'>{dec}</b></span><br>"
                f"<span style='font-family:JetBrains Mono;font-size:12px;color:#6b7280;'>Approver: {hs.key_output.get('approver','approver')}</span></div>"
                f"<div style='margin-top:10px;font-size:13px;color:#4b5563;'>{str(hs.key_output.get('brief',''))[:300]}</div></div>", unsafe_allow_html=True)
        else:
            st.info("No HITL step in this pipeline.")
        if es:
            c1,c2 = st.columns(2)
            with c1: st.metric("Exit Code", es.key_output.get("exit_code","N/A"))
            with c2:
                rows = es.key_output.get("rows_affected")
                st.metric("Rows Affected", f"{rows:,}" if rows else "N/A")
            scr = es.key_output.get("script","")
            if scr:
                st.markdown("**Script Executed:**"); st.code(scr, language="sql")
        if exec_report:
            st.markdown(f"<div style='background:#f8f9fb;border:1px solid #e5e7eb;border-radius:8px;padding:14px;font-family:JetBrains Mono;font-size:12px;color:#1f2937;white-space:pre-wrap;'>{exec_report}</div>", unsafe_allow_html=True)
        if ss:
            st.markdown("---"); st.markdown("**Scheduling Agent**")
            c1,c2 = st.columns(2)
            with c1: st.metric("Event",   ss.key_output.get("event","N/A"))
            with c2:
                summ = ss.key_output.get("summary","")
                st.metric("Summary",(summ[:40]+"…") if len(summ)>40 else (summ or "N/A"))
        if not hs and not es and not ss:
            st.info("No execution-layer agents ran in this pipeline.")

    # TAB 5 ── Audit Trail ────────────────────────────────────────────────────
    with t5:
        st.markdown("#### Audit & Compliance")
        a_s = _step(result,"audit")
        viols   = a_s.key_output.get("violations",0) if a_s else 0
        anomals = len(a_s.full_state.get("anomalies",[])) if a_s else 0
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.metric("Total Events",     len(result.all_audit_events))
        with c2: st.metric("Policy Violations",viols)
        with c3: st.metric("Anomalies",        anomals)
        with c4: st.metric("Compliance",       f"{compliance:.0%}")
        st.markdown("---")
        for evt in result.all_audit_events[:40]:
            ok  = "✓" if evt.get("policy_ok",True) else "✗"
            col = "#059669" if evt.get("policy_ok",True) else "#dc2626"
            st.markdown(
                f"<div style='font-family:JetBrains Mono;font-size:11px;padding:3px 0;"
                f"border-bottom:1px solid #f3f4f6;color:#6b7280;'>"
                f"<span style='color:{col};'>{ok}</span> "
                f"<span style='color:#9ca3af;'>{str(evt.get('timestamp',''))[:19]}</span>  "
                f"<span style='color:#1d4ed8;'>{evt.get('agent_type','?')}</span>::"
                f"<span style='color:#d97706;'>{evt.get('node_name','?')}</span>  "
                f"<span style='color:#374151;'>{evt.get('action','?')}</span></div>",
                unsafe_allow_html=True)
        if audit_rpt:
            with st.expander("📋 Full Audit Report (JSON)"):
                st.json(audit_rpt if isinstance(audit_rpt, dict) else {})

    # TAB 6 ── Raw State ──────────────────────────────────────────────────────
    with t6:
        if show_raw:
            st.markdown("#### Full Agent State (JSON)")
            for step in result.steps:
                with st.expander(f"[{step.step_id}] {step.step_label}"):
                    safe = {k:v for k,v in step.full_state.items() if not isinstance(v,(bytes,bytearray))}
                    try: st.json(safe)
                    except Exception: st.code(str(safe)[:5000])
        else:
            st.info("Enable 'Show raw state' checkbox to view full agent state JSON.")

    st.divider()
    st.markdown(
        f"<div style='font-family:JetBrains Mono;font-size:11px;color:#9ca3af;text-align:center;'>"
        f"run_id: {result.run_id}  ·  session: {result.session_id}  ·  "
        f"{result.started_at[:19]} → {result.completed_at[:19]}</div>",
        unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    # st.markdown("### ◉ Agentic AI Accelerator")
    # st.caption("Multi-agent pipeline · 21 agents · 5 UCs + custom · v4")
    # st.divider()

    # st.markdown("**API Configuration**")
    # api_key = st.text_input("Anthropic API Key", type="password",
    #                          placeholder="sk-ant-... (optional)")
    # if api_key:
    #     os.environ["ANTHROPIC_API_KEY"] = api_key
    #     st.success("✓ API key set — using Claude")
    # else:
    #     st.info("ℹ Using Mock LLM (no key required)")

    # st.divider()
    # st.markdown("**Mode**")
    # mode = st.radio("Mode", ["Production Use Cases","✨ Custom (Auto-Orchestrated)"],
    #                 label_visibility="collapsed")

    mode = st.radio("Mode", ["Use Cases"], label_visibility="collapsed")
    
    if mode == "Use Cases":
        selected_label = st.selectbox("Use Case", UC_LABELS, label_visibility="collapsed")
        selected_uc = _uc_by_label(selected_label)
        bc = selected_uc["badge_color"]
        st.markdown(
            f"<div style='background:{bc}18;border:1px solid {bc}44;border-radius:8px;"
            f"padding:8px 12px;margin-top:6px;'>"
            f"<div style='font-size:10px;font-weight:600;color:{bc};letter-spacing:1px;text-transform:uppercase;'>"
            f"{selected_uc['agent_count']} agents active</div>"
            f"<div style='font-size:11px;color:#4b5563;margin-top:4px;line-height:1.5;'>{selected_uc['description']}</div>"
            f"</div>", unsafe_allow_html=True)
    else:
        selected_uc = None
        st.markdown(
            "<div style='background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;"
            "padding:8px 12px;margin-top:6px;'>"
            "<div style='font-size:10px;font-weight:600;color:#0369a1;letter-spacing:1px;text-transform:uppercase;'>Auto-Orchestrated</div>"
            "<div style='font-size:11px;color:#4b5563;margin-top:4px;line-height:1.5;'>"
            "LLM analyses your prompt, selects agents, builds and runs the pipeline dynamically.</div>"
            "</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("**All 21 Agents**")
    active_set = set(selected_uc["agents"]) if selected_uc else set()
    lg: dict = {0:[],1:[],2:[],3:[]}
    for ak,(layer,icon,color,name) in ALL_AGENT_LAYERS.items():
        lg[layer].append((ak,icon,color,name))
    for ln in [0,1,2,3]:
        col = LAYER_COLORS[ln]
        st.markdown(f"<div class='sidebar-label' style='color:{col};margin-top:10px;'>{LAYER_NAMES[ln]}</div>", unsafe_allow_html=True)
        for ak,icon,color,name in lg[ln]:
            active = ak in active_set
            dot = f"<span style='color:{color};font-size:7px;'>●</span> " if active else ""
            st.markdown(f"<div style='font-family:JetBrains Mono;font-size:11px;color:#6b7280;padding:1px 8px;opacity:{'1.0' if active else '0.28'};'>{dot}{icon} {name}</div>", unsafe_allow_html=True)

#     st.divider()
#     st.markdown("""<div style='font-size:11px;color:#9ca3af;line-height:1.7;'>
# <b style='color:#6b7280'>Stack</b><br>LangGraph · LangChain · Anthropic Claude<br>
# Langfuse · Agentic AI Accelerator v4</div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────

if selected_uc:
    preview = " → ".join(STEP_DISPLAY.get(a,(a,))[0] for a in selected_uc["agents"][:8]) + (" → …" if len(selected_uc["agents"])>8 else "")
else:
    preview = "Prompt → AutoOrchestrator → LLM selects agents → Dynamic pipeline → Results"

st.markdown(f"""
<div style='margin-bottom:1.8rem;padding-bottom:1.2rem;border-bottom:1px solid #e5e7eb;'>
    <h1 style='margin:0;'>Agentic AI Accelerator</h1>
</div>""", unsafe_allow_html=True)
# <div style='margin-bottom:1.8rem;padding-bottom:1.2rem;border-bottom:1px solid #e5e7eb;'>
#     <div style='font-size:11px;color:#1d4ed8;letter-spacing:1.5px;text-transform:uppercase;font-weight:600;margin-bottom:6px;'>
#         ◉ LangGraph Multi-Agent Pipeline · Generalised Orchestration Layer · v4
#     </div>
#     <h1 style='margin:0;'>Agentic AI Accelerator</h1>
#     <p style='color:#6b7280;font-size:14px;margin-top:4px;'>{preview}</p>
# </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# INPUT & CONTROLS
# ─────────────────────────────────────────────────────────────────────────────

if selected_uc:
    if ("last_uc_key" not in st.session_state or
            st.session_state["last_uc_key"] != selected_uc["key"]):
        st.session_state["last_uc_key"] = selected_uc["key"]
        st.session_state["input_text"]  = selected_uc["prompt"]
        st.session_state.pop("pipeline_result", None)
        st.session_state.pop("auto_result", None)

    user_input = st.text_area("Input",
        value=st.session_state.get("input_text", selected_uc["prompt"]),
        height=185, label_visibility="collapsed")

    col1,col2,col3 = st.columns([2,1,1])
    with col1: run_btn = st.button(f"▶  Run {selected_uc['short']} — {selected_uc['agent_count']} Agents", use_container_width=True)
    with col2:
        if st.button("↺  Reset", use_container_width=True):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
    with col3: show_raw = st.checkbox("Show raw state", False)
    preview_btn = False

else:
    # ── Custom Auto-Orchestrated mode ─────────────────────────────────────────
    if "last_uc_key" in st.session_state and st.session_state["last_uc_key"] != "custom":
        st.session_state.pop("pipeline_result", None); st.session_state.pop("auto_result", None)
    st.session_state["last_uc_key"] = "custom"

    st.markdown("""<div style='background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;padding:14px 18px;margin-bottom:14px;'>
  <div style='font-size:11px;font-weight:600;color:#0369a1;letter-spacing:0.8px;text-transform:uppercase;margin-bottom:6px;'>✨ Custom Use Case — Auto-Orchestrated</div>
  <div style='font-size:13px;color:#0c4a6e;line-height:1.6;'>
    Type <b>any business request</b> below. The AutoOrchestrator analyses it with the LLM,
    selects agents from all 21 available, builds the pipeline dynamically, executes it,
    and passes <b>AgentResponse</b> messages between agents automatically.
  </div>
</div>""", unsafe_allow_html=True)

    EXAMPLES = [
        "Analyse Q3 sales data, identify underperforming regions and draft a recovery plan.",
        "Parse the vendor invoice, validate against SAP POs, flag discrepancies and notify procurement.",
        "Translate the customer complaint from French to English, search KB and draft a response.",
        "Generate a competitive analysis on AI infra market trends and schedule a strategy review.",
    ]
    example = st.selectbox("Try an example:", ["— type your own —"] + EXAMPLES)
    user_input = st.text_area("Your custom request:",
        value="" if example == "— type your own —" else example,
        height=150, placeholder="Describe any business process in plain English…")

    col1,col2,col3,col4 = st.columns([3,1,1,1])
    with col1: run_btn = st.button("✨  Analyse & Run Auto-Pipeline", use_container_width=True)
    with col2: preview_btn = st.button("🔍  Preview Plan", use_container_width=True)
    with col3:
        if st.button("↺  Reset", use_container_width=True):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
    with col4: show_raw = st.checkbox("Show raw state", False)

    # ── Preview Plan (no execution) ───────────────────────────────────────────
    if preview_btn and user_input.strip():
        with st.spinner("Analysing and building plan…"):
            try:
                plan = analyse_request(user_input.strip())
                cfg  = build_auto_pipeline(user_input.strip(), plan=plan)
                st.markdown("#### 🔍 Auto-Orchestration Plan Preview")
                st.info(f"**{plan.use_case_title}** · {plan.reasoning}")
                cols = st.columns(min(len(cfg.steps), 7))
                for i, step in enumerate(cfg.steps):
                    lc = LAYER_COLORS.get(step.layer,"#6b7280")
                    icon = ALL_AGENT_LAYERS.get(step.agent,(0,"·","#6b7280",step.agent))[1]
                    with cols[i % len(cols)]:
                        st.markdown(f"<div style='text-align:center;background:{lc}12;border:1px solid {lc}44;border-radius:8px;padding:10px;'>"
                            f"<div style='font-size:18px;color:{lc};'>{icon}</div>"
                            f"<div style='font-size:10px;color:{lc};font-weight:600;margin-top:4px;'>{step.agent}</div>"
                            f"<div style='font-size:9px;color:#6b7280;'>{step.label[:18]}</div>"
                            f"<div style='font-size:9px;color:#9ca3af;'>L{step.layer}</div></div>", unsafe_allow_html=True)
                st.caption("Execution order: " + " → ".join(s.agent for s in cfg.steps))
            except Exception as e:
                st.error(f"Plan analysis failed: {e}")

st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE EXECUTION
# ─────────────────────────────────────────────────────────────────────────────

if run_btn and user_input.strip():

    if selected_uc:
        # ── Production UC ─────────────────────────────────────────────────────
        cfg = selected_uc["config"]
        step_ids = [s.id for s in cfg.steps]
        st.markdown("### Pipeline Execution")
        pph, pbar, ptext = _step_indicators(step_ids)
        on_step = _make_on_step(pph, pbar, ptext, len(step_ids))
        with st.spinner("Running pipeline …"):
            result = run_pipeline(cfg, user_input.strip(), on_step=on_step)
        pbar.progress(1.0)
        fc = len([s for s in result.steps if s.status=="FAILED"])
        ptext.markdown(
            "<span style='font-family:JetBrains Mono;font-size:12px;color:#059669;'>✓ All agents completed</span>"
            if fc==0 else
            f"<span style='font-family:JetBrains Mono;font-size:12px;color:#d97706;'>⚠ {fc} step(s) failed</span>",
            unsafe_allow_html=True)
        st.session_state["pipeline_result"] = result
        st.session_state["pipeline_uc_key"] = selected_uc["key"]
        st.session_state.pop("auto_result", None)

    else:
        # ── Custom Auto-Orchestrated ──────────────────────────────────────────
        sid = new_id("auto")
        st.markdown("### ✨ Auto-Orchestrating Pipeline")
        status_ph = st.empty()
        status_ph.info("🔍 Step 1/3 — Analysing request and selecting agents…")
        plan_ph = st.empty()
        pbar    = st.progress(0)
        ptext   = st.empty()

        with st.spinner("Running auto-orchestrated pipeline…"):
            try:
                auto_res: AutoPipelineResult = run_auto(
                    user_input=user_input.strip(),
                    session_id=sid,
                    verbose=False,
                )
                result = auto_res.pipeline_result
            except Exception as exc:
                st.error(f"Auto-orchestration failed: {exc}")
                st.stop()

        pbar.progress(1.0)
        plan = auto_res.plan
        status_ph.success(
            f"✓ Pipeline complete — **{plan.use_case_title}** · "
            f"{len(auto_res.execution_order)} agents · "
            f"{auto_res.steps_completed}/{len(auto_res.execution_order)} completed")

        # Show selected agents visually
        with plan_ph.container():
            st.markdown(f"**Rationale:** {plan.reasoning}")
            cols = st.columns(min(len(auto_res.execution_order), 7))
            for i, ak in enumerate(auto_res.execution_order):
                meta = ALL_AGENT_LAYERS.get(ak,(0,"·","#6b7280",ak))
                lc = LAYER_COLORS.get(meta[0],"#6b7280")
                with cols[i % len(cols)]:
                    st.markdown(f"<div style='text-align:center;background:{lc}12;border:1px solid {lc}44;border-radius:8px;padding:8px;'>"
                        f"<div style='font-size:16px;color:{lc};'>{meta[1]}</div>"
                        f"<div style='font-size:10px;color:{lc};font-weight:600;'>{ak}</div>"
                        f"<div style='font-size:9px;color:#9ca3af;'>L{meta[0]}</div></div>", unsafe_allow_html=True)

        fc = auto_res.steps_failed
        ptext.markdown(
            "<span style='font-family:JetBrains Mono;font-size:12px;color:#059669;'>✓ Pipeline completed</span>"
            if fc==0 else
            f"<span style='font-family:JetBrains Mono;font-size:12px;color:#d97706;'>⚠ {fc} step(s) failed</span>",
            unsafe_allow_html=True)

        st.session_state["pipeline_result"] = result
        st.session_state["auto_result"]     = auto_res
        st.session_state["pipeline_uc_key"] = "custom"


# ─────────────────────────────────────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────────────────────────────────────

if "pipeline_result" in st.session_state:
    result   = st.session_state["pipeline_result"]
    ruc_key  = st.session_state.get("pipeline_uc_key","")
    auto_res = st.session_state.get("auto_result")
    if ruc_key == "custom" and auto_res:
        ruc = {"short":"Custom · Auto-Orchestrated","description":auto_res.plan.use_case_title,
               "badge_color":"#7c3aed","agent_count":len(auto_res.execution_order)}
    else:
        ruc = next((u for u in USE_CASES if u["key"]==ruc_key),
                   selected_uc if selected_uc else USE_CASES[0])
    _render_results(result, ruc, show_raw, auto_res=auto_res)


# ─────────────────────────────────────────────────────────────────────────────
# WELCOME SCREEN
# ─────────────────────────────────────────────────────────────────────────────

elif not run_btn:
    cards = ""
    # for uc in USE_CASES:
    #     bcc = uc["badge_color"]
    #     ag  = " · ".join(uc["agents"][:5]) + (" · …" if len(uc["agents"])>5 else "")
    #     cards += f"""
    # <div style='background:{bcc}0d;border:1px solid {bcc}30;border-radius:9px;padding:14px 16px;'>
    #   <div style='color:{bcc};font-size:10px;font-weight:600;letter-spacing:1px;text-transform:uppercase;'>{uc["short"]} — {uc["agent_count"]} agents</div>
    #   <div style='color:#1f2937;margin-top:4px;font-size:13px;font-weight:600;'>{uc["label"].split(" · ")[1].rsplit("  ",1)[0]}</div>
    #   <div style='color:#6b7280;margin-top:4px;font-size:11px;line-height:1.5;'>{uc["description"]}</div>
    #   <div style='margin-top:6px;font-family:JetBrains Mono;font-size:10px;color:{bcc};'>{ag}</div>
    # </div>"""

#     st.markdown(f"""
# <div style='background:#ffffff;border:1px solid #e5e7eb;border-radius:14px;padding:28px 32px;margin:12px 0;box-shadow:0 1px 4px rgba(0,0,0,0.06);'>
#   <h3 style='margin-top:0;color:#111827;'>Generalised Multi-Agent Pipeline — 21 Agents · 5 Use Cases + Custom</h3>
#   <p style='color:#6b7280;line-height:1.7;'>
#     Choose a <b>production use case</b> from the sidebar or switch to <b>✨ Custom</b> to type any
#     business request — the AutoOrchestrator selects agents and builds the pipeline automatically.
#   </p>
#   <div style='background:#f0f9ff;border:1px solid #bae6fd;border-radius:9px;padding:12px 16px;margin:14px 0;'>
#     <b style='color:#0369a1;font-size:12px;'>✨ Custom Mode</b>
#     <span style='color:#0c4a6e;font-size:12px;'> — Type any prompt. The LLM analyses intent, selects from all 21 agents,
#     builds the pipeline via <code>auto_orchestrator.py</code>, and streams AgentResponse messages between agents.</span>
#   </div>
#   <div style='display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:18px;'>{cards}</div>
#   <div style='display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;margin-top:14px;'>
#     <div style='background:#eff6ff;border:1px solid #bfdbfe;border-radius:9px;padding:10px;'>
#       <div style='color:#1d4ed8;font-size:10px;font-weight:600;text-transform:uppercase;'>Layer 0</div>
#       <div style='color:#1f2937;font-size:12px;margin-top:2px;'><b>Router</b></div></div>
#     <div style='background:#f5f3ff;border:1px solid #ddd6fe;border-radius:9px;padding:10px;'>
#       <div style='color:#7c3aed;font-size:10px;font-weight:600;text-transform:uppercase;'>Layer 1</div>
#       <div style='color:#1f2937;font-size:12px;margin-top:2px;'><b>Intent · Planner · Workflow</b></div></div>
#     <div style='background:#f0fdf4;border:1px solid #bbf7d0;border-radius:9px;padding:10px;'>
#       <div style='color:#059669;font-size:10px;font-weight:600;text-transform:uppercase;'>Layer 2</div>
#       <div style='color:#1f2937;font-size:12px;margin-top:2px;'><b>14 agents</b> — Intel · Data · Integration</div></div>
#     <div style='background:#fef2f2;border:1px solid #fecaca;border-radius:9px;padding:10px;'>
#       <div style='color:#dc2626;font-size:10px;font-weight:600;text-transform:uppercase;'>Layer 3</div>
#       <div style='color:#1f2937;font-size:12px;margin-top:2px;'><b>HITL · Execution · Audit · Notif · Scheduling</b></div></div>
#   </div>
#   <div style='margin-top:14px;padding:10px 14px;background:#f8f9fb;border-radius:8px;font-family:JetBrains Mono;font-size:11px;color:#6b7280;'>
#     💡 No API key required — runs fully offline with the deterministic Mock LLM
#   </div>
# </div>""", unsafe_allow_html=True)
