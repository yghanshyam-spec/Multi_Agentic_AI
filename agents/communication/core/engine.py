"""
communication/core/engine.py
Main orchestration engine for the Communication Agent accelerator.
"""
from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from communication.core.provider import LLMProvider
from shared.langfuse_manager import get_prompt as _get_prompt_lf
from communication.utils.config_loader import ConfigLoader
from shared.common import get_logger
from communication.workflows.create_graph import GraphFactory
from communication.schemas.output_models import (
    AgentResponse, OmnichannelResponse, BroadcastResponse, ErrorResponse
)

logger = get_logger(__name__)


class CommunicationAgentEngine:
    """
    Central engine for the Communication Agent accelerator.

    Usage:
        engine = CommunicationAgentEngine(config_path="config/agent_config.yaml")
        result = engine.run(
            workflow="omnichannel_response",
            inbound_payload={"channel": "email", "sender": "...", "body": "..."},
        )
    """

    def __init__(
        self,
        config_path: str = "config/agent_config.yaml",
        env_file: Optional[str] = ".env",
        config_dict: Optional[Dict[str, Any]] = None,
    ):
        if env_file and os.path.exists(env_file):
            load_dotenv(env_file, override=True)
            logger.info(f"Loaded environment from {env_file}")

        self._loader = ConfigLoader()
        self.agent_config = (
            self._loader.load_dict(config_dict) if config_dict
            else self._loader.load(config_path)
        )

        # LLM / prompt config -- inline section or standalone file
        self._llm_config = (
            self.agent_config if "llm" in self.agent_config
            else self._loader.load("config/llm_config.yaml")
        )
        self._prompts_config = (
            self.agent_config if "prompts" in self.agent_config
            else self._loader.load("config/prompts_config.yaml")
        )

        self._llm_provider = LLMProvider(self._llm_config.get("llm", {}))
        self.llm = self._llm_provider.get_client()
        self._langfuse = LangfuseClient(self.agent_config)
        self._prompt_manager = PromptManager(self._prompts_config, self._langfuse)

        self._graph_cache: Dict[str, Any] = {}
        self._graph_factory = GraphFactory(
            llm=self.llm,
            prompt_manager=self._prompt_manager,
            agent_config=self.agent_config,
            langfuse_client=self._langfuse,
        )
        logger.info("CommunicationAgentEngine ready")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def run(
        self,
        workflow: str,
        user_message: str = "",
        session_id: Optional[str] = None,
        inbound_payload: Optional[Dict[str, Any]] = None,
        talking_points: Optional[str] = None,
        target_channels: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        session_id = session_id or str(uuid.uuid4())
        trace_id   = str(uuid.uuid4())

        trace = self._langfuse.start_trace(
            name=f"comm_agent.{workflow}",
            session_id=session_id,
            input={"workflow": workflow, "user_message": user_message[:200]},
            metadata=metadata or {},
            trace_id=trace_id,
        )

        try:
            graph = self._get_or_build_graph(workflow)
            state = self._build_initial_state(
                workflow=workflow, user_message=user_message,
                session_id=session_id, trace_id=trace_id,
                inbound_payload=inbound_payload or {},
                talking_points=talking_points,
                target_channels=target_channels,
                metadata=metadata,
            )
            final_state = graph.invoke(state)
            response = self._build_response(workflow, final_state, session_id, trace_id)
            self._langfuse.end_trace(trace, output=response.dict())
            return response

        except Exception as exc:
            logger.error(f"Workflow '{workflow}' failed: {exc}", exc_info=True)
            self._langfuse.end_trace(trace, error=str(exc))
            return ErrorResponse(
                session_id=session_id, workflow=workflow, success=False,
                message=f"Workflow failed: {exc}", trace_id=trace_id, error_detail=str(exc),
            )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _get_or_build_graph(self, workflow: str):
        if workflow not in self._graph_cache:
            wf_path = (
                self.agent_config.get("workflows", {})
                .get(workflow, {})
                .get("graph_config")
            )
            if not wf_path:
                raise ValueError(f"No graph_config defined for workflow '{workflow}'")
            wf_config = self._loader.load(wf_path)
            self._graph_cache[workflow] = self._graph_factory.build(wf_config)
        return self._graph_cache[workflow]

    def _build_initial_state(
        self, workflow: str, user_message: str, session_id: str,
        trace_id: str, inbound_payload: Dict, talking_points: Optional[str],
        target_channels: Optional[List[str]], metadata: Optional[Dict],
    ) -> Dict[str, Any]:
        base = {
            "user_message": user_message,
            "session_id":   session_id,
            "trace_id":     trace_id,
            "workflow":     workflow,
            "metadata":     metadata or {},
            "current_node": None,
            "error":        None,
        }
        if workflow == "omnichannel_response":
            return {**base,
                    "inbound_payload":       inbound_payload,
                    "normalised_message":    None,
                    "detected_channel":      None,
                    "conversation_history":  [],
                    "context_summary":       None,
                    "classification":        None,
                    "draft_response":        None,
                    "preferred_reply_channel": None,
                    "channel_rules":         None,
                    "consistency_report":    None,
                    "dispatch_results":      [],
                    "crm_logged":            False,
                    "audit_entry":           None}
        elif workflow == "broadcast_drafting":
            return {**base,
                    "inbound_payload":       inbound_payload,
                    "talking_points":        talking_points or user_message,
                    "target_channels":       target_channels or [],
                    "normalised_message":    None,
                    "detected_channel":      None,
                    "conversation_history":  [],
                    "context_summary":       None,
                    "classification":        None,
                    "channel_drafts":        [],
                    "draft_response":        None,
                    "consistency_report":    None,
                    "consistency_fixed":     False,
                    "dispatch_results":      [],
                    "audit_entry":           None}
        return {**base, "inbound_payload": inbound_payload, "dispatch_results": []}

    def _build_response(
        self, workflow: str, state: Dict[str, Any],
        session_id: str, trace_id: str,
    ) -> AgentResponse:
        err = state.get("error")
        if workflow == "omnichannel_response":
            msg_obj = state.get("normalised_message") or {}
            cls     = state.get("classification") or {}
            draft   = state.get("draft_response", "")
            dispatch= state.get("dispatch_results", [])
            audit   = state.get("audit_entry") or {}
            success = not bool(err)
            message = draft or (f"Error: {err}" if err else "Workflow complete.")
            return OmnichannelResponse(
                session_id=session_id, workflow=workflow, success=success,
                message=message, trace_id=trace_id,
                thread_id=msg_obj.get("thread_id"),
                detected_channel=state.get("detected_channel"),
                classification=cls.get("classification"),
                priority=cls.get("priority"),
                sentiment=cls.get("sentiment"),
                draft_response=draft,
                reply_channel=state.get("preferred_reply_channel"),
                dispatch_results=dispatch,
                crm_logged=state.get("crm_logged", False),
                requires_human=cls.get("requires_human", False),
                audit_id=audit.get("audit_id"),
            )
        elif workflow == "broadcast_drafting":
            drafts  = state.get("channel_drafts", [])
            report  = state.get("consistency_report") or {}
            dispatch= state.get("dispatch_results", [])
            audit   = state.get("audit_entry") or {}
            contradictions = report.get("contradictions", [])
            success = not bool(err)
            message = (
                f"Broadcast drafts created for {len(drafts)} channel(s). "
                f"Consistent: {report.get('is_consistent', True)}."
                if success else f"Error: {err}"
            )
            return BroadcastResponse(
                session_id=session_id, workflow=workflow, success=success,
                message=message, trace_id=trace_id,
                target_channels=[d["channel"] for d in drafts],
                channel_drafts=drafts,
                is_consistent=report.get("is_consistent", True),
                contradictions=contradictions,
                dispatch_results=dispatch,
                audit_id=audit.get("audit_id"),
            )
        return AgentResponse(
            session_id=session_id, workflow=workflow,
            success=not bool(err),
            message=err or "Workflow completed.",
            trace_id=trace_id,
        )
