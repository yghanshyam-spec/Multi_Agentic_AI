"""
communication/schemas/output_models.py
Pydantic response models returned by CommunicationAgentEngine.run().
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    session_id: str
    workflow: str
    success: bool
    message: str
    trace_id: Optional[str] = None

    def dict(self, **kwargs) -> Dict[str, Any]:
        return super().model_dump(**kwargs)


class OmnichannelResponse(AgentResponse):
    thread_id: Optional[str] = None
    detected_channel: Optional[str] = None
    classification: Optional[str] = None
    priority: Optional[str] = None
    sentiment: Optional[str] = None
    draft_response: Optional[str] = None
    reply_channel: Optional[str] = None
    dispatch_results: List[Dict[str, Any]] = Field(default_factory=list)
    crm_logged: bool = False
    requires_human: bool = False
    audit_id: Optional[str] = None


class BroadcastResponse(AgentResponse):
    target_channels: List[str] = Field(default_factory=list)
    channel_drafts: List[Dict[str, Any]] = Field(default_factory=list)
    is_consistent: bool = True
    contradictions: List[str] = Field(default_factory=list)
    dispatch_results: List[Dict[str, Any]] = Field(default_factory=list)
    audit_id: Optional[str] = None


class ErrorResponse(AgentResponse):
    success: bool = False
    error_detail: Optional[str] = None
