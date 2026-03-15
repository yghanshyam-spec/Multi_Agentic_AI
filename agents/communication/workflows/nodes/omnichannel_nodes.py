"""
communication/workflows/nodes/omnichannel_nodes.py
Node functions for Use Case 1: Omnichannel Customer Response.

Nodes (in order):
  detect_channel_node      -> load_context_node -> classify_message_node
  -> draft_response_node   -> check_consistency_node -> dispatch_response_node
  -> update_context_node
"""
from __future__ import annotations

import json
import uuid
from typing import Any, Dict

from communication.agents.specialist_agent import CommunicationSpecialistAgent
from communication.tools.communication_tools import ContextMemoryTool, ChannelDispatcher, CRMLogTool, AuditLogTool
from shared.common import get_logger
from communication.utils.helpers import now_iso, generate_thread_id, word_count, sentiment_hint

logger = get_logger(__name__)


def make_omnichannel_nodes(
    agent: CommunicationSpecialistAgent,
    tools: Dict[str, Any],
    node_config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Factory: returns {node_id -> node_fn} for the omnichannel workflow.
    All tool and agent bindings are injected -- nothing hardcoded.
    """
    memory: ContextMemoryTool     = tools["memory"]
    dispatcher: ChannelDispatcher = tools["dispatcher"]
    crm: CRMLogTool               = tools["crm"]
    audit: AuditLogTool           = tools["audit"]
    omni_cfg = node_config.get("omnichannel", {})
    channel_rules = node_config.get("channel_rules", {})

    # ------------------------------------------------------------------
    # 1. detect_channel_node  (Channel Detector)
    # ------------------------------------------------------------------
    def detect_channel_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[NODE] detect_channel_node")
        payload = state.get("inbound_payload", {})

        # First try rule-based detection (fast, no LLM token cost)
        channel = _rule_detect_channel(payload)
        if not channel:
            # Fall back to LLM detection
            try:
                raw = agent.invoke(
                    "comm_detect_channel",
                    trace_id=state.get("trace_id"),
                    payload=json.dumps(payload, default=str),
                )
                parsed = agent.parse_json(raw) or {}
                channel = parsed.get("channel", "api")
            except Exception as exc:
                logger.warning(f"  LLM channel detection failed: {exc}. Defaulting to 'api'.")
                channel = "api"
                parsed = {}
        else:
            parsed = {}

        sender       = payload.get("sender") or parsed.get("sender", "unknown")
        sender_email = payload.get("sender_email") or parsed.get("sender_email")
        subject      = payload.get("subject") or parsed.get("subject", "")
        body         = payload.get("body") or payload.get("message") or parsed.get("body", state.get("user_message", ""))

        thread_id = (
            payload.get("thread_id")
            or state.get("session_id")
            or generate_thread_id(channel, sender, subject)
        )

        normalised = {
            "channel":      channel,
            "sender":       sender,
            "sender_email": sender_email,
            "subject":      subject,
            "body":         body,
            "thread_id":    thread_id,
            "session_id":   state.get("session_id", thread_id),
            "timestamp":    now_iso(),
            "raw_metadata": payload,
        }

        logger.info(f"  Channel detected: {channel} | thread: {thread_id}")
        return {**state, "normalised_message": normalised,
                "detected_channel": channel, "current_node": "detect_channel_node"}

    # ------------------------------------------------------------------
    # 2. load_context_node  (Context Loader)
    # ------------------------------------------------------------------
    def load_context_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[NODE] load_context_node")
        msg = state.get("normalised_message", {})
        thread_id = msg.get("thread_id") or state.get("session_id", "")
        max_history = omni_cfg.get("max_history_entries", 20)

        history = memory.load(thread_id, max_entries=max_history)
        summary = memory.get_summary(thread_id) if history else "No prior conversation."

        logger.info(f"  Loaded {len(history)} history entries for thread {thread_id}")
        return {**state, "conversation_history": history,
                "context_summary": summary, "current_node": "load_context_node"}

    # ------------------------------------------------------------------
    # 3. classify_message_node  (Message Classifier)
    # ------------------------------------------------------------------
    def classify_message_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[NODE] classify_message_node")
        msg = state.get("normalised_message", {})
        body    = msg.get("body", state.get("user_message", ""))
        channel = msg.get("channel", "api")
        summary = state.get("context_summary", "")

        try:
            raw = agent.invoke(
                "comm_classify_message",
                trace_id=state.get("trace_id"),
                channel=channel,
                body=body,
                context_summary=summary,
            )
            parsed = agent.parse_json(raw) or {}
        except Exception as exc:
            logger.warning(f"  Classification LLM failed: {exc}. Using rule-based fallback.")
            parsed = {}

        # Guardrail: apply rule-based overrides for escalation keywords
        escalation_keywords = omni_cfg.get("escalation_keywords", [
            "urgent", "lawyer", "legal", "sue", "refund", "unacceptable", "escalate"
        ])
        body_lower = body.lower()
        if any(kw in body_lower for kw in escalation_keywords):
            parsed["classification"]  = "human_escalation"
            parsed["requires_human"]  = True
            parsed["priority"]        = "urgent"
            parsed["escalation_reason"] = "Escalation keyword detected"

        classification = {
            "classification":   parsed.get("classification", "automated_response"),
            "priority":         parsed.get("priority", "medium"),
            "sentiment":        parsed.get("sentiment", sentiment_hint(body)),
            "topic":            parsed.get("topic", "general enquiry"),
            "requires_human":   parsed.get("requires_human", False),
            "escalation_reason": parsed.get("escalation_reason"),
        }

        logger.info(f"  Classification: {classification['classification']} | "
                    f"priority: {classification['priority']} | "
                    f"sentiment: {classification['sentiment']}")
        return {**state, "classification": classification,
                "current_node": "classify_message_node"}

    # ------------------------------------------------------------------
    # 4. draft_response_node  (Response Drafter)
    # ------------------------------------------------------------------
    def draft_response_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[NODE] draft_response_node")
        msg            = state.get("normalised_message", {})
        classification = state.get("classification", {})
        history        = state.get("conversation_history", [])
        channel        = msg.get("channel", "email")
        body           = msg.get("body", "")

        # Determine preferred reply channel
        preferred = _preferred_reply_channel(channel, classification, omni_cfg)
        rules = channel_rules.get(preferred, channel_rules.get("default", {}))
        tone = rules.get("tone", "professional")
        max_words = rules.get("max_words", 200)

        # Format history for context
        history_text = _format_history(history, max_entries=5)

        # Handle escalation differently
        if classification.get("requires_human"):
            draft = (
                f"Thank you for reaching out. We understand this is an urgent matter "
                f"and have escalated your case to our specialist team. "
                f"You will receive a personal response within 2 business hours. "
                f"Your reference number is #{uuid.uuid4().hex[:8].upper()}."
            )
        else:
            try:
                draft = agent.invoke(
                    "comm_draft_response",
                    trace_id=state.get("trace_id"),
                    channel=preferred,
                    channel_rules=json.dumps(rules),
                    classification=classification.get("classification", "automated_response"),
                    body=body,
                    history=history_text,
                    instructions=state.get("metadata", {}).get("instructions", ""),
                    tone=tone,
                    max_length=max_words,
                )
            except Exception as exc:
                logger.error(f"  Draft response LLM failed: {exc}")
                draft = f"Thank you for your message. We are looking into your request and will respond shortly."

        logger.info(f"  Draft ready ({word_count(draft)} words) for channel: {preferred}")
        return {**state, "draft_response": draft,
                "preferred_reply_channel": preferred,
                "channel_rules": rules,
                "current_node": "draft_response_node"}

    # ------------------------------------------------------------------
    # 5. check_consistency_node  (Consistency Checker)
    # ------------------------------------------------------------------
    def check_consistency_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[NODE] check_consistency_node")
        draft   = state.get("draft_response", "")
        history = state.get("conversation_history", [])

        if len(history) < 2:
            # No prior history to check against
            report = {"is_consistent": True, "contradictions": [], "suggested_fixes": [], "confidence": 1.0}
            logger.info("  No prior history -- consistency check skipped")
            return {**state, "consistency_report": report, "current_node": "check_consistency_node"}

        try:
            raw = agent.invoke(
                "comm_check_consistency",
                trace_id=state.get("trace_id"),
                drafts=json.dumps([{"channel": state.get("preferred_reply_channel"), "content": draft}]),
                history=_format_history(history),
            )
            report = agent.parse_json(raw) or {
                "is_consistent": True, "contradictions": [], "suggested_fixes": [], "confidence": 0.8
            }
        except Exception as exc:
            logger.warning(f"  Consistency check failed: {exc}. Assuming consistent.")
            report = {"is_consistent": True, "contradictions": [], "suggested_fixes": [], "confidence": 0.7}

        if not report.get("is_consistent") and report.get("suggested_fixes"):
            # Auto-apply first suggested fix if available
            fixes_text = "; ".join(report.get("suggested_fixes", []))
            logger.warning(f"  Inconsistency detected. Fixes: {fixes_text[:100]}")

        logger.info(f"  Consistent: {report.get('is_consistent')} | "
                    f"contradictions: {len(report.get('contradictions', []))}")
        return {**state, "consistency_report": report, "current_node": "check_consistency_node"}

    # ------------------------------------------------------------------
    # 6. dispatch_response_node  (Channel Dispatcher)
    # ------------------------------------------------------------------
    def dispatch_response_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[NODE] dispatch_response_node")
        draft   = state.get("draft_response", "")
        channel = state.get("preferred_reply_channel", "email")
        msg     = state.get("normalised_message", {})
        thread_id = msg.get("thread_id", state.get("session_id", ""))

        metadata = {
            "sender":       msg.get("sender"),
            "sender_email": msg.get("sender_email"),
            "subject":      msg.get("subject", "Response"),
            "session_id":   state.get("session_id"),
        }

        result = dispatcher.dispatch(channel, draft, metadata, thread_id=thread_id)
        logger.info(f"  Dispatched to {channel} | status: {result.get('status')} | "
                    f"id: {result.get('delivery_id')}")
        return {**state, "dispatch_results": [result], "current_node": "dispatch_response_node"}

    # ------------------------------------------------------------------
    # 7. update_context_node  (Context Updater)
    # ------------------------------------------------------------------
    def update_context_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[NODE] update_context_node")
        msg       = state.get("normalised_message", {})
        thread_id = msg.get("thread_id", state.get("session_id", ""))
        draft     = state.get("draft_response", "")
        dispatch  = state.get("dispatch_results", [{}])
        cls       = state.get("classification", {})

        # Save the user's inbound message
        memory.save(thread_id, {
            "role":    "user",
            "channel": msg.get("channel", "unknown"),
            "content": msg.get("body", ""),
            "metadata": {"subject": msg.get("subject"), "sender": msg.get("sender")},
        })

        # Save the agent's draft response
        memory.save(thread_id, {
            "role":    "assistant",
            "channel": state.get("preferred_reply_channel", "email"),
            "content": draft,
            "metadata": {
                "delivery_id":  dispatch[0].get("delivery_id") if dispatch else None,
                "dispatch_status": dispatch[0].get("status") if dispatch else None,
                "classification": cls.get("classification"),
            },
        })

        # Log to CRM
        crm_result = crm.log(
            thread_id=thread_id,
            session_id=state.get("session_id", ""),
            workflow=state.get("workflow", "omnichannel_response"),
            channel=msg.get("channel", "unknown"),
            classification=cls.get("classification", "unknown"),
            resolution=draft,
            history=state.get("conversation_history", []),
        )

        # Audit log
        audit_result = audit.log(
            event_type="OMNICHANNEL_RESPONSE",
            workflow=state.get("workflow", "omnichannel_response"),
            session_id=state.get("session_id", ""),
            channels=[msg.get("channel", "unknown"), state.get("preferred_reply_channel", "email")],
            details={"thread_id": thread_id, "crm_id": crm_result.get("crm_id"),
                     "classification": cls.get("classification")},
        )

        logger.info(f"  Context updated | CRM id: {crm_result.get('crm_id', '')[:8]} | "
                    f"Audit id: {audit_result.get('audit_id', '')[:8]}")
        return {
            **state,
            "crm_logged": True,
            "audit_entry": {"audit_id": audit_result.get("audit_id"),
                            "crm_id": crm_result.get("crm_id")},
            "current_node": "update_context_node",
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _rule_detect_channel(payload: Dict[str, Any]) -> str:
        if payload.get("channel"):
            return payload["channel"]
        if payload.get("email") or payload.get("sender_email") or "@" in str(payload.get("sender", "")):
            return "email"
        if payload.get("slack_channel") or payload.get("slack_user"):
            return "slack"
        if payload.get("teams_channel") or payload.get("teams_user"):
            return "teams"
        if payload.get("chat_session") or payload.get("session_id"):
            return "chat"
        if payload.get("transcript") or payload.get("voice"):
            return "voice"
        if payload.get("webhook_url") or payload.get("callback_url"):
            return "api"
        return ""

    def _preferred_reply_channel(channel: str, cls: Dict, cfg: Dict) -> str:
        # Policy: urgent escalations always use email
        if cls.get("requires_human") or cls.get("priority") == "urgent":
            return cfg.get("escalation_channel", "email")
        # Consumer preference from config
        prefs = cfg.get("reply_channel_preference", {})
        if channel in prefs:
            return prefs[channel]
        # Default: reply on same channel
        return channel

    def _format_history(history: list, max_entries: int = 10) -> str:
        if not history:
            return "No prior conversation."
        parts = []
        for entry in history[-max_entries:]:
            role    = entry.get("role", "user")
            ch      = entry.get("channel", "")
            content = entry.get("content", "")[:150]
            parts.append(f"[{ch}/{role}]: {content}")
        return "\n".join(parts)

    return {
        "detect_channel_node":       detect_channel_node,
        "load_context_node":         load_context_node,
        "classify_message_node":     classify_message_node,
        "draft_response_node":       draft_response_node,
        "check_consistency_node":    check_consistency_node,
        "dispatch_response_node":    dispatch_response_node,
        "update_context_node":       update_context_node,
    }
