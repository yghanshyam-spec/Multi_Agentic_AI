from __future__ import annotations
"""agents/vector_query/graph.py — Vector Query (RAG) Agent."""
from shared import (
    BaseAgentState, AgentType, ExecutionStatus,
    BaseAgentState, AgentMessage, ExecutionMetadata,
    make_base_state, build_agent_response, make_audit_event,
)

from shared.langfuse_manager import get_tracer
from agents.vector_query.nodes.vector_query_nodes import (
    preprocess_query_node,embed_query_node,retrieve_chunks_node,filter_chunks_node,
    rerank_chunks_node,generate_response_node,check_faithfulness_node,update_memory_node)

# ── Workflow node imports (split files: one node per file) ────────────────────
# These are the canonical imports — use workflows/nodes/<node>.py for each node.
# The legacy agents/vector_query/nodes/ location is preserved for backward compatibility.
from agents.vector_query.workflows.nodes import (
    preprocess_query_node, embed_query_node, retrieve_chunks_node, filter_chunks_node, rerank_chunks_node, generate_response_node, check_faithfulness_node, update_memory_node,
)


def run_vector_query_agent(raw_input:str,session_id:str=None,agent_config:dict=None)->dict:
    """RAG pipeline: query expansion → embed → retrieve → rerank → generate → faithfulness check.
    Consumer config: vector_store.type/table, embedding_model, top_k, filters.min_score,
    prompts.preprocess / generate / faithfulness.
    """
    state=make_base_state(raw_input,AgentType.VECTOR_QUERY,session_id=session_id)
    state.update({"expanded_queries":[],"original_query":raw_input,"query_embedding":[],
        "embedding_model":None,"retrieved_chunks":[],"filtered_chunks":[],"reranked_chunks":[],
        "generated_answer":None,"retrieved_context":None,"faithful":True,"unsupported_claims":[],
        "conversation_history":[],"config":agent_config or {}})
    tracer=get_tracer("vector_query_agent")
    with tracer.trace("rag_workflow",session_id=state["session_id"],input=raw_input[:200],
                      metadata={"run_id": state.get("run_id",""), "correlation_id": state.get("correlation_id","")}):
        for fn in [preprocess_query_node,embed_query_node,retrieve_chunks_node,filter_chunks_node,
                   rerank_chunks_node,generate_response_node,check_faithfulness_node,update_memory_node]:
            state={**state,**fn(state)}
    tracer.flush()
    # ── Build standard AgentResponse envelope ────────────────────────────
    state["agent_response"] = dict(build_agent_response(
        state,
        payload={"result": state.get("generated_answer")},
        confidence_score=state.get("working_memory", {}).get("confidence", 0.90),
    ))
    # ── Emit a terminal audit event ────────────────────────────────────────
    state.setdefault("audit_events", []).append(
        make_audit_event(state, "run_vector_query_agent", "AGENT_COMPLETED")
    )
    return state
