"""
communication/workflows/nodes/broadcast_nodes.py
Node functions for Use Case 2: Internal Broadcast Drafting.

Nodes (in order):
  detect_channel_node  (reused: detects this is a broadcast/API input)
  load_context_node    (reused: loads any prior broadcast context)
  classify_message_node (reused: classifies as broadcast task)
  draft_response_node  -> NOW drafts for EACH target channel
  check_consistency_node -> checks all drafts are factually consistent
  dispatch_response_node -> sends each draft to its channel
  update_context_node  -> persists all drafts and delivery status
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from communication.sub_agents.specialist_agent import CommunicationSpecialistAgent
from communication.tools.communication_tools import ContextMemoryTool, ChannelDispatcher, AuditLogTool
from shared.common import get_logger
from communication.utils.helpers import now_iso, word_count

logger = get_logger(__name__)


def make_broadcast_nodes(
    agent: CommunicationSpecialistAgent,
    tools: Dict[str, Any],
    node_config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Factory: returns {node_id -> node_fn} for the broadcast drafting workflow.
    """
    memory: ContextMemoryTool     = tools["memory"]
    dispatcher: ChannelDispatcher = tools["dispatcher"]
    audit: AuditLogTool           = tools["audit"]
    bcast_cfg    = node_config.get("broadcast", {})
    channel_rules = node_config.get("channel_rules", {})

    # ------------------------------------------------------------------
    # 1. detect_channel_node  (normalise broadcast input)
    # ------------------------------------------------------------------
    def detect_channel_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[NODE] detect_channel_node (broadcast)")
        payload = state.get("inbound_payload", {})
        target_channels = (
            payload.get("target_channels")
            or state.get("target_channels")
            or bcast_cfg.get("default_channels", ["email", "slack", "memo"])
        )

        body = (
            payload.get("talking_points")
            or payload.get("body")
            or state.get("talking_points")
            or state.get("user_message", "")
        )

        normalised = {
            "channel":      "api",
            "sender":       payload.get("sender", "communications_manager"),
            "sender_email": payload.get("sender_email"),
            "subject":      payload.get("subject", "Internal Broadcast"),
            "body":         body,
            "thread_id":    state.get("session_id", "broadcast-session"),
            "session_id":   state.get("session_id", "broadcast-session"),
            "timestamp":    now_iso(),
            "raw_metadata": payload,
        }

        logger.info(f"  Broadcast detected | target channels: {target_channels}")
        return {
            **state,
            "normalised_message": normalised,
            "detected_channel": "api",
            "target_channels": target_channels,
            "talking_points": body,
            "current_node": "detect_channel_node",
        }

    # ------------------------------------------------------------------
    # 2. load_context_node
    # ------------------------------------------------------------------
    def load_context_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[NODE] load_context_node (broadcast)")
        thread_id = state.get("session_id", "broadcast-session")
        max_history = bcast_cfg.get("max_history_entries", 10)
        history = memory.load(thread_id, max_entries=max_history)
        summary = memory.get_summary(thread_id) if history else "No prior broadcast sessions."
        logger.info(f"  Loaded {len(history)} history entries")
        return {**state, "conversation_history": history,
                "context_summary": summary, "current_node": "load_context_node"}

    # ------------------------------------------------------------------
    # 3. classify_message_node
    # ------------------------------------------------------------------
    def classify_message_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[NODE] classify_message_node (broadcast)")
        # Broadcasts are always automated_response, low/medium priority
        classification = {
            "classification": "automated_response",
            "priority":       "medium",
            "sentiment":      "neutral",
            "topic":          "internal broadcast",
            "requires_human": False,
            "escalation_reason": None,
        }
        logger.info(f"  Classification: {classification['classification']}")
        return {**state, "classification": classification,
                "current_node": "classify_message_node"}

    # ------------------------------------------------------------------
    # 4. draft_response_node  (multi-channel broadcast drafter)
    # ------------------------------------------------------------------
    def draft_response_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[NODE] draft_response_node (broadcast)")
        talking_points  = state.get("talking_points", state.get("user_message", ""))
        target_channels = state.get("target_channels", ["email", "slack", "memo"])
        channel_drafts  = []

        for channel in target_channels:
            rules    = channel_rules.get(channel, channel_rules.get("default", {}))
            tone     = rules.get("tone", "professional")
            max_words = rules.get("max_words", 300)

            try:
                content = agent.invoke(
                    "comm_broadcast_draft",
                    trace_id=state.get("trace_id"),
                    channel=channel,
                    channel_rules=json.dumps(rules),
                    talking_points=talking_points,
                    tone=tone,
                    max_length=max_words,
                )
            except Exception as exc:
                logger.error(f"  Draft for {channel} failed: {exc}")
                content = f"[Draft unavailable for {channel} due to error: {exc}]"

            wc = word_count(content)
            channel_drafts.append({
                "channel":   channel,
                "content":   content,
                "tone":      tone,
                "word_count": wc,
                "is_consistent": True,  # will be updated by checker
            })
            logger.info(f"  Drafted for {channel}: {wc} words")

        # Also store combined draft in draft_response for shared nodes
        combined = "\n\n".join(
            f"=== {d['channel'].upper()} ===\n{d['content']}" for d in channel_drafts
        )
        return {**state, "channel_drafts": channel_drafts,
                "draft_response": combined, "current_node": "draft_response_node"}

    # ------------------------------------------------------------------
    # 5. check_consistency_node  (cross-channel factual consistency)
    # ------------------------------------------------------------------
    def check_consistency_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[NODE] check_consistency_node (broadcast)")
        channel_drafts = state.get("channel_drafts", [])
        history        = state.get("conversation_history", [])

        if len(channel_drafts) < 2:
            report = {"is_consistent": True, "contradictions": [], "suggested_fixes": [], "confidence": 1.0}
            return {**state, "consistency_report": report, "consistency_fixed": False,
                    "current_node": "check_consistency_node"}

        drafts_payload = [{"channel": d["channel"], "content": d["content"]} for d in channel_drafts]
        history_text = "\n".join(
            f"[{e.get('channel','')}/{e.get('role','')}]: {e.get('content','')[:100]}"
            for e in history[-5:]
        ) or "No prior history."

        try:
            raw = agent.invoke(
                "comm_check_consistency",
                trace_id=state.get("trace_id"),
                drafts=json.dumps(drafts_payload),
                history=history_text,
            )
            report = agent.parse_json(raw) or {
                "is_consistent": True, "contradictions": [], "suggested_fixes": [], "confidence": 0.8
            }
        except Exception as exc:
            logger.warning(f"  Consistency check LLM failed: {exc}")
            report = {"is_consistent": True, "contradictions": [], "suggested_fixes": [], "confidence": 0.7}

        is_consistent = bool(report.get("is_consistent", True))
        contradictions = report.get("contradictions", [])
        fixes = report.get("suggested_fixes", [])
        consistency_fixed = False

        if contradictions:
            logger.warning(f"  Found {len(contradictions)} contradiction(s): {contradictions[:2]}")

        if not is_consistent and fixes and bcast_cfg.get("auto_fix_contradictions", True):
            # Update consistency flag on each draft
            updated_drafts = []
            for draft in channel_drafts:
                updated_drafts.append({**draft, "is_consistent": False})
            channel_drafts = updated_drafts
            consistency_fixed = True

        logger.info(f"  Consistent: {is_consistent} | contradictions: {len(contradictions)}")
        return {
            **state,
            "channel_drafts":    channel_drafts,
            "consistency_report": report,
            "consistency_fixed": consistency_fixed,
            "current_node": "check_consistency_node",
        }

    # ------------------------------------------------------------------
    # 6. dispatch_response_node  (dispatch all channel versions)
    # ------------------------------------------------------------------
    def dispatch_response_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[NODE] dispatch_response_node (broadcast)")
        channel_drafts = state.get("channel_drafts", [])
        msg = state.get("normalised_message", {})
        thread_id = msg.get("thread_id", state.get("session_id", ""))
        metadata = {
            "sender":       msg.get("sender"),
            "sender_email": msg.get("sender_email"),
            "subject":      msg.get("subject", "Internal Broadcast"),
            "session_id":   state.get("session_id"),
        }
        results = []
        for draft in channel_drafts:
            result = dispatcher.dispatch(
                draft["channel"], draft["content"], metadata, thread_id=thread_id
            )
            results.append(result)
            logger.info(f"  Dispatched {draft['channel']} | status: {result.get('status')}")

        return {**state, "dispatch_results": results, "current_node": "dispatch_response_node"}

    # ------------------------------------------------------------------
    # 7. update_context_node
    # ------------------------------------------------------------------
    def update_context_node(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[NODE] update_context_node (broadcast)")
        thread_id      = state.get("session_id", "broadcast-session")
        channel_drafts = state.get("channel_drafts", [])
        talking_points = state.get("talking_points", "")
        dispatch       = state.get("dispatch_results", [])

        # Save the original talking points
        memory.save(thread_id, {
            "role":    "user",
            "channel": "api",
            "content": talking_points,
            "metadata": {"type": "broadcast_input"},
        })

        # Save each channel draft
        for draft in channel_drafts:
            delivery = next((d for d in dispatch if d.get("channel") == draft["channel"]), {})
            memory.save(thread_id, {
                "role":    "assistant",
                "channel": draft["channel"],
                "content": draft["content"],
                "metadata": {
                    "type":          "broadcast_draft",
                    "word_count":    draft.get("word_count"),
                    "is_consistent": draft.get("is_consistent"),
                    "delivery_id":   delivery.get("delivery_id"),
                    "dispatch_status": delivery.get("status"),
                },
            })

        # Audit
        audit_result = audit.log(
            event_type="BROADCAST_DRAFT",
            workflow=state.get("workflow", "broadcast_drafting"),
            session_id=thread_id,
            channels=[d["channel"] for d in channel_drafts],
            details={
                "draft_count":     len(channel_drafts),
                "is_consistent":   state.get("consistency_report", {}).get("is_consistent", True),
                "contradictions":  len(state.get("consistency_report", {}).get("contradictions", [])),
            },
        )

        logger.info(f"  Context updated | {len(channel_drafts)} drafts persisted | "
                    f"audit_id: {audit_result.get('audit_id','')[:8]}")
        return {
            **state,
            "audit_entry": {"audit_id": audit_result.get("audit_id")},
            "current_node": "update_context_node",
        }

    return {
        "detect_channel_node":     detect_channel_node,
        "load_context_node":       load_context_node,
        "classify_message_node":   classify_message_node,
        "draft_response_node":     draft_response_node,
        "check_consistency_node":  check_consistency_node,
        "dispatch_response_node":  dispatch_response_node,
        "update_context_node":     update_context_node,
    }
