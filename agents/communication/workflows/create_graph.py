"""
communication/workflows/create_graph.py
Dynamic LangGraph assembly from YAML workflow configuration.
"""
from __future__ import annotations

import importlib
from typing import Any, Callable, Dict, Optional

from langgraph.graph import StateGraph, END

from communication.sub_agents.specialist_agent import CommunicationSpecialistAgent
from communication.tools.communication_tools import (
    ContextMemoryTool, ChannelDispatcher, CRMLogTool, AuditLogTool
)
from communication.workflows.nodes.omnichannel_nodes import make_omnichannel_nodes
from communication.workflows.nodes.broadcast_nodes import make_broadcast_nodes
from communication.workflows.edges import build_conditional_router
from shared.common import get_logger

logger = get_logger(__name__)


class GraphFactory:
    """Assembles and compiles a LangGraph from YAML workflow configuration."""

    def __init__(self, llm: Any, prompt_manager: Any,
                 agent_config: Dict[str, Any], langfuse_client: Any = None):
        self.llm = llm
        self.prompt_manager = prompt_manager
        self.agent_config = agent_config
        self.langfuse = langfuse_client

        self.agent = CommunicationSpecialistAgent(
            llm=llm, prompt_manager=prompt_manager,
            langfuse_client=langfuse_client, agent_config=agent_config,
        )

        # Shared tools -- initialised from consumer config
        channels_cfg = agent_config.get("channels", {})
        self.tools = {
            "memory":     ContextMemoryTool(),
            "dispatcher": ChannelDispatcher(channels_cfg),
            "crm":        CRMLogTool(),
            "audit":      AuditLogTool(),
        }

    def build(self, workflow_config: Dict[str, Any]):
        wf = workflow_config.get("workflow", {})
        workflow_name = wf.get("name", "unknown")
        entry_point   = wf.get("entry_point")
        nodes_cfg     = workflow_config.get("nodes", [])
        edges_cfg     = workflow_config.get("edges", [])
        node_config   = workflow_config.get("node_config", {})

        logger.info(f"Building graph: {workflow_name}")

        # Resolve state schema
        state_schema = self._resolve_state_schema(wf.get("state_schema"))

        # Build node functions
        if workflow_name == "omnichannel_response":
            node_fns = make_omnichannel_nodes(self.agent, self.tools, node_config)
        elif workflow_name == "broadcast_drafting":
            node_fns = make_broadcast_nodes(self.agent, self.tools, node_config)
        else:
            node_fns = self._build_generic_nodes(nodes_cfg)

        graph = StateGraph(state_schema)

        # Register nodes
        for nc in nodes_cfg:
            nid = nc["id"]
            if nc.get("type") == "end_node":
                continue
            fn = node_fns.get(nid)
            if fn is None:
                logger.warning(f"No function for node '{nid}', skipping")
                continue
            fn = self._wrap_obs(fn, nid)
            graph.add_node(nid, fn)
            logger.debug(f"  + Node: {nid}")

        # Register edges
        for ec in edges_cfg:
            from_node = ec["from"]
            to_node   = ec["to"]
            edge_type = ec.get("type", "direct")

            if not any(n["id"] == from_node for n in nodes_cfg):
                continue

            actual_to = END if to_node == "end" else to_node

            if edge_type == "direct":
                graph.add_edge(from_node, actual_to)
            elif edge_type == "conditional":
                cfield = ec.get("condition_field", "")
                routes_raw = ec.get("routes", {})
                routes = {k: (END if v == "end" else v) for k, v in routes_raw.items()}
                router = build_conditional_router(cfield, routes, default=ec.get("default"))
                graph.add_conditional_edges(from_node, router)
            elif edge_type == "named":
                import workflows.edges as _edges
                fn = getattr(_edges, ec.get("function", ""), None)
                if fn:
                    graph.add_conditional_edges(from_node, fn)

        graph.set_entry_point(entry_point)
        compiled = graph.compile()
        logger.info(f"Graph '{workflow_name}' compiled ({len(nodes_cfg)} nodes)")
        return compiled

    def _resolve_state_schema(self, schema_path: Optional[str]):
        if not schema_path:
            from communication.schemas.graph_state import GenericCommState
            return GenericCommState
        try:
            parts = schema_path.rsplit(".", 1)
            module = importlib.import_module(parts[0])
            return getattr(module, parts[1])
        except Exception as exc:
            logger.warning(f"Cannot resolve schema '{schema_path}': {exc}")
            from communication.schemas.graph_state import GenericCommState
            return GenericCommState

    def _build_generic_nodes(self, nodes_cfg) -> Dict[str, Callable]:
        fns = {}
        for nc in nodes_cfg:
            nid = nc["id"]
            if nc.get("type") == "end_node":
                continue
            def _noop(state, _id=nid):
                logger.info(f"[NODE-GENERIC] {_id}")
                return {**state, "current_node": _id}
            fns[nid] = _noop
        return fns

    def _wrap_obs(self, fn: Callable, node_id: str) -> Callable:
        if not self.langfuse:
            return fn
        def wrapped(state: Dict[str, Any]) -> Dict[str, Any]:
            span = self.langfuse.start_span(f"node.{node_id}", trace_id=state.get("trace_id"))
            try:
                result = fn(state)
                self.langfuse.end_span(span, output={"node": node_id})
                return result
            except Exception as exc:
                self.langfuse.end_span(span, error=str(exc))
                raise
        return wrapped
