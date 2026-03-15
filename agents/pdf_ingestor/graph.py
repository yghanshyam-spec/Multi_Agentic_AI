from __future__ import annotations
"""agents/pdf_ingestor/graph.py"""
from shared import (
    BaseAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

from shared.langfuse_manager import get_tracer
from agents.pdf_ingestor.nodes.pdf_ingestor_nodes import (
    trigger_ingestion_node, extract_text_node, clean_text_node, classify_sections_node,
    chunk_documents_node, embed_chunks_node, upsert_vectors_node, audit_ingestion_node,
)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/pdf_ingestor/nodes/ location is preserved for backward compatibility.
from agents.pdf_ingestor.workflows.nodes import (
    trigger_ingestion_node, extract_text_node, clean_text_node, classify_sections_node, chunk_documents_node, embed_chunks_node, upsert_vectors_node, audit_ingestion_node,
)


def run_pdf_ingestor_agent(raw_input: str, pdf_path: str = None, session_id: str = None, agent_config: dict = None) -> dict:
    """Ingest a PDF into a vector store.
    Consumer config: chunk_size, embedding_model, vector_store.type/host/table,
    prompts.classify_sections / prompts.audit.
    """
    state = make_base_state(raw_input, AgentType.PDF_INGESTOR, session_id=session_id)
    state.update({"pdf_path":pdf_path or raw_input,"ingestion_id":None,"extracted_pages":[],
        "page_count":0,"is_scanned":False,"cleaned_pages":[],"document_sections":[],
        "chunks":[],"chunk_count":0,"embedded_chunks":[],"upsert_result":{},"ingestion_summary":{},
        "config":agent_config or {}})
    tracer=get_tracer("pdf_ingestor_agent")
    with tracer.trace("pdf_ingestion_workflow",session_id=state["session_id"],input=str(pdf_path,
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")})[:100]):
        for fn in [trigger_ingestion_node,extract_text_node,clean_text_node,classify_sections_node,
                   chunk_documents_node,embed_chunks_node,upsert_vectors_node,audit_ingestion_node]:
            state={**state,**fn(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("ingestion_summary")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_pdf_ingestor_agent", "AGENT_COMPLETED")
    )
    return state
