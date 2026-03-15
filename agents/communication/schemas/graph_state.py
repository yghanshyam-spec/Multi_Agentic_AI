"""
communication/schemas/graph_state.py
TypedDict state schemas for all communication workflow graphs.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class NormalisedMessage(TypedDict, total=False):
    channel: str          # email | chat | slack | teams | api | voice | memo
    sender: str
    sender_email: Optional[str]
    subject: Optional[str]
    body: str
    thread_id: str
    session_id: str
    timestamp: str
    raw_metadata: Dict[str, Any]


class MessageClassification(TypedDict, total=False):
    classification: str   # automated_response | human_escalation | acknowledgement_only
    priority: str         # low | medium | high | urgent
    sentiment: str        # positive | neutral | negative
    topic: str
    requires_human: bool
    escalation_reason: Optional[str]


class ChannelDraft(TypedDict, total=False):
    channel: str
    content: str
    tone: str
    word_count: int
    is_consistent: bool


class ConsistencyReport(TypedDict, total=False):
    is_consistent: bool
    contradictions: List[str]
    suggested_fixes: List[str]
    confidence: float


class DispatchResult(TypedDict, total=False):
    channel: str
    status: str           # sent | queued | failed | simulated
    delivery_id: Optional[str]
    timestamp: str
    error: Optional[str]


class ContextEntry(TypedDict, total=False):
    role: str             # user | assistant | system
    channel: str
    content: str
    timestamp: str
    metadata: Dict[str, Any]


# ---- Use Case 1: Omnichannel Customer Response ------------------------------

class OmnichannelState(TypedDict, total=False):
    # Input
    user_message: str
    inbound_payload: Dict[str, Any]
    session_id: str
    trace_id: str
    workflow: str
    metadata: Dict[str, Any]

    # Detected & normalised message
    normalised_message: Optional[NormalisedMessage]
    detected_channel: Optional[str]

    # Context
    conversation_history: List[ContextEntry]
    context_summary: Optional[str]

    # Classification
    classification: Optional[MessageClassification]

    # Response drafting
    draft_response: Optional[str]
    preferred_reply_channel: Optional[str]
    channel_rules: Optional[Dict[str, Any]]

    # Consistency
    consistency_report: Optional[ConsistencyReport]

    # Dispatch
    dispatch_results: List[DispatchResult]

    # Audit / CRM
    crm_logged: bool
    audit_entry: Optional[Dict[str, Any]]

    # Control flow
    current_node: Optional[str]
    error: Optional[str]


# ---- Use Case 2: Internal Broadcast Drafting --------------------------------

class BroadcastState(TypedDict, total=False):
    # Input
    user_message: str
    talking_points: str
    target_channels: List[str]
    session_id: str
    trace_id: str
    workflow: str
    metadata: Dict[str, Any]

    # Context
    conversation_history: List[ContextEntry]
    context_summary: Optional[str]

    # Classification (simple for broadcasts)
    classification: Optional[MessageClassification]

    # Channel drafts
    channel_drafts: List[ChannelDraft]
    consistency_report: Optional[ConsistencyReport]
    consistency_fixed: bool

    # Dispatch
    dispatch_results: List[DispatchResult]

    # Audit
    audit_entry: Optional[Dict[str, Any]]

    # Control
    current_node: Optional[str]
    error: Optional[str]


# ---- Generic fallback -------------------------------------------------------

class GenericCommState(TypedDict, total=False):
    user_message: str
    session_id: str
    trace_id: str
    workflow: str
    metadata: Dict[str, Any]
    normalised_message: Optional[NormalisedMessage]
    conversation_history: List[ContextEntry]
    draft_response: Optional[str]
    dispatch_results: List[DispatchResult]
    current_node: Optional[str]
    error: Optional[str]
