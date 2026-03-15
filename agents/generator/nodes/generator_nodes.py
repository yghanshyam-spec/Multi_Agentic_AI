"""agents/generator/nodes/generator_nodes.py
Canonical implementation file. Imported by workflows/nodes/ split files.
"""
from __future__ import annotations
import os
import time
from shared import (GeneratorAgentState, ExecutionStatus, build_agent_response,
    make_audit_event, utc_now, new_id, get_llm, call_llm, build_trace_entry)
from shared.langfuse_manager import get_prompt, log_llm_call
from shared.llm_factory import get_last_token_usage
from agents.generator.prompts.defaults import get_default_prompt
from agents.generator.tools.template_library import TEMPLATES, get_template, list_templates

def _p(key, state, **kw):
    fb = state.get("config",{}).get("prompts",{}).get(key) or get_default_prompt(f"generator_{key}")
    return get_prompt(f"generator_{key}", agent_name="generator", fallback=fb, **kw)

def select_template_node(state):
    t0 = time.monotonic()
    sys_p = _p("select", state, request=state["raw_input"], templates=list_templates())
    result = call_llm(get_llm(), sys_p, f"Select for: {state['raw_input']}", node_hint="select_template")
    log_llm_call("generator_agent","select_template_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(result),state.get("session_id",""), token_usage=get_last_token_usage())
    tid = result.get("template_id","incident_report_v2")
    return {"template_id": tid, "generation_config": get_template(tid), "status": ExecutionStatus.RUNNING,
            "current_node": "select_template_node",
            "execution_trace": [build_trace_entry("select_template_node", int((time.monotonic()-t0)*1000), 150)],
            "audit_events": [make_audit_event(state,"select_template_node",f"TEMPLATE:{tid}")]}

def collect_inputs_node(state):
    t0 = time.monotonic()
    wm = state.get("working_memory", {})
    collected = {"incident_summary": wm.get("incident_summary",state["raw_input"]),
        "root_cause": wm.get("root_cause","Missing composite index on orders(created_at, status)"),
        "resolution": wm.get("resolution","CREATE INDEX CONCURRENTLY applied successfully"),
        "timeline": wm.get("timeline",["14:15 UTC - Deployment v2.3.1","14:32 UTC - Alert triggered","15:04 UTC - Fix applied"]),
        "affected_service": wm.get("affected_service","order_processing_api"),
        "business_impact": wm.get("business_impact","~£24,000 in delayed order completions"),
        "reasoning_chain": wm.get("reasoning_chain",[])}
    return {"collected_inputs": collected, "current_node": "collect_inputs_node",
            "execution_trace": [build_trace_entry("collect_inputs_node", int((time.monotonic()-t0)*1000))]}

def plan_content_node(state):
    t0 = time.monotonic()
    tmpl = state.get("generation_config", {})
    sys_p = _p("plan", state, template=tmpl.get("name","Document"), inputs=state.get("collected_inputs",{}), audience=tmpl.get("audience","general"))
    result = call_llm(get_llm(), sys_p, "Plan outline", node_hint="plan_content")
    return {"content_outline": result, "current_node": "plan_content_node",
            "execution_trace": [build_trace_entry("plan_content_node", int((time.monotonic()-t0)*1000), 200)]}

def generate_section_node(state):
    t0 = time.monotonic()
    tmpl = state.get("generation_config", {})
    outline = state.get("content_outline", {})
    inputs = state.get("collected_inputs", {})
    sections_plan = outline.get("sections",[{"id":"exec_summary","title":"Executive Summary"},{"id":"timeline","title":"Incident Timeline"},{"id":"root_cause","title":"Root Cause Analysis"},{"id":"resolution","title":"Resolution & Prevention"}])
    generated = []
    for sec in sections_plan:
        sys_p = _p("section", state, section=sec.get("title",sec.get("id")), doc_type=tmpl.get("name","Report"),
                   outline=sec.get("key_points",[]), data=inputs, audience=tmpl.get("audience","general"))
        result = call_llm(get_llm(), sys_p, f"Write: {sec.get('title')}", node_hint="generate_section")
        generated.append({"section_id":sec.get("id"),"title":sec.get("title"),"content":result.get("content",result.get("raw_response",f"## {sec.get('title')}\n\n[Content]"))})
    log_llm_call("generator_agent","generate_section_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),"[section prompts]",str(len(generated))+" sections",state.get("session_id",""), token_usage=get_last_token_usage())
    return {"generated_sections": generated, "current_node": "generate_section_node",
            "execution_trace": [build_trace_entry("generate_section_node", int((time.monotonic()-t0)*1000), 600)]}

def review_content_node(state):
    t0 = time.monotonic()
    sections = state.get("generated_sections", [])
    full = "\n\n".join(s.get("content","") for s in sections)
    sys_p = _p("review", state, content=full[:2000])
    result = call_llm(get_llm(), sys_p, "Review content", node_hint="review_content")
    return {"review_result": result, "current_node": "review_content_node",
            "execution_trace": [build_trace_entry("review_content_node", int((time.monotonic()-t0)*1000), 200)]}

def refine_content_node(state):
    t0 = time.monotonic()
    review = state.get("review_result", {})
    sections = state.get("generated_sections", [])
    full = "\n\n".join(s.get("content","") for s in sections)
    if not review.get("revision_needed", False):
        return {"refined_content": full, "current_node": "refine_content_node",
                "execution_trace": [build_trace_entry("refine_content_node", int((time.monotonic()-t0)*1000))]}
    sys_p = _p("refine", state, content=full, feedback=review.get("issues",[]))
    result = call_llm(get_llm(), sys_p, "Refine", node_hint="refine_content")
    log_llm_call("generator_agent","refine_content_node",os.getenv("ANTHROPIC_MODEL", os.getenv("OPENAI_MODEL", "claude-sonnet-4-6")),sys_p[:200],str(result),state.get("session_id",""), token_usage=get_last_token_usage())
    return {"refined_content": result.get("refined_content",full), "current_node": "refine_content_node",
            "execution_trace": [build_trace_entry("refine_content_node", int((time.monotonic()-t0)*1000), 250)]}

def assemble_document_node(state):
    t0 = time.monotonic()
    tmpl = state.get("generation_config", {})
    inputs = state.get("collected_inputs", {})
    refined = state.get("refined_content", "")
    sections = state.get("generated_sections", [])
    header = f"# {tmpl.get('name','Incident Report')}\n**Generated**: {utc_now()}\n**Service**: {inputs.get('affected_service','N/A')}\n**Status**: RESOLVED ✓\n---\n"
    body = refined if refined else "\n\n".join(f"## {s.get('title','')}\n\n{s.get('content','')}" for s in sections)
    final_doc = header + body + "\n\n---\n*Generated by Agentic AI Accelerator — Generator Agent*"
    response = build_agent_response(state, payload={"template_id":state.get("template_id"),"document_title":tmpl.get("name","Report"),
        "sections_count":len(sections),"final_document":final_doc,"review_score":state.get("review_result",{}).get("score",9),
        "word_count":len(final_doc.split())}, confidence_score=0.93)
    return {"final_document": final_doc, "agent_response": dict(response), "status": ExecutionStatus.COMPLETED,
            "current_node": "assemble_document_node",
            "execution_trace": [build_trace_entry("assemble_document_node", int((time.monotonic()-t0)*1000))],
            "audit_events": [make_audit_event(state,"assemble_document_node","DOCUMENT_ASSEMBLED")]}
