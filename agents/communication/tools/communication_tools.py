"""
communication/tools/communication_tools.py

All channel tools: memory store, channel adapters (mock + real stubs),
CRM logger, and channel dispatcher. All mock by default.
"""
from __future__ import annotations

import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from shared.common import get_logger
from communication.utils.helpers import now_iso

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# In-memory stores (replaced by Redis / DB in production)
# ---------------------------------------------------------------------------

_CONVERSATION_STORE: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
_CRM_LOG: List[Dict[str, Any]] = []
_DISPATCH_LOG: List[Dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Memory / Context Store
# ---------------------------------------------------------------------------

class ContextMemoryTool:
    """
    Retrieves and persists conversation history keyed by thread_id/session_id.
    Mock: in-memory dict. Production: replace with Redis, DynamoDB, Cosmos DB.
    """

    def load(self, thread_id: str, max_entries: int = 20) -> List[Dict[str, Any]]:
        history = _CONVERSATION_STORE.get(thread_id, [])
        return history[-max_entries:]

    def save(self, thread_id: str, entry: Dict[str, Any]) -> bool:
        _CONVERSATION_STORE[thread_id].append({**entry, "timestamp": now_iso()})
        logger.debug(f"[MEMORY] Saved entry for thread {thread_id}")
        return True

    def get_summary(self, thread_id: str) -> str:
        history = self.load(thread_id, max_entries=5)
        if not history:
            return "No prior conversation history."
        parts = []
        for entry in history:
            role = entry.get("role", "user")
            channel = entry.get("channel", "unknown")
            content = entry.get("content", "")[:100]
            parts.append(f"[{channel}/{role}] {content}")
        return " | ".join(parts)

    def update_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        if thread_id not in _CONVERSATION_STORE:
            return False
        # Append a metadata marker entry
        _CONVERSATION_STORE[thread_id].append({
            "role": "system",
            "channel": "internal",
            "content": f"[METADATA UPDATE] {json.dumps(metadata)}",
            "timestamp": now_iso(),
        })
        return True

    @staticmethod
    def all_threads() -> List[str]:
        return list(_CONVERSATION_STORE.keys())


# ---------------------------------------------------------------------------
# Channel Adapters (mock -- replace with real SDK calls)
# ---------------------------------------------------------------------------

class EmailAdapter:
    """Mock SMTP/SendGrid adapter."""

    def __init__(self, config: Dict[str, Any]):
        self._mock = str(config.get("mock_mode", "true")).lower() == "true"
        self._smtp_host = config.get("smtp_host", "")
        self._from_addr = config.get("from_address", "agent@company.com")

    def send(self, to: str, subject: str, body: str,
             thread_id: Optional[str] = None) -> Dict[str, Any]:
        delivery_id = str(uuid.uuid4())[:8]
        if self._mock:
            logger.info(f"[EMAIL-MOCK] To: {to} | Subject: {subject[:50]} | id={delivery_id}")
            _DISPATCH_LOG.append({
                "channel": "email", "to": to, "subject": subject,
                "body_preview": body[:100], "delivery_id": delivery_id,
                "thread_id": thread_id, "timestamp": now_iso(), "status": "simulated",
            })
            return {"status": "simulated", "delivery_id": delivery_id, "channel": "email"}
        # Production: real SMTP/API call here
        return {"status": "sent", "delivery_id": delivery_id, "channel": "email"}


class SlackAdapter:
    """Mock Slack API adapter."""

    def __init__(self, config: Dict[str, Any]):
        self._mock = str(config.get("mock_mode", "true")).lower() == "true"
        self._webhook_url = config.get("slack_webhook_url", "")
        self._default_channel = config.get("slack_channel", "#general")

    def send(self, channel: str, text: str,
             thread_id: Optional[str] = None) -> Dict[str, Any]:
        delivery_id = str(uuid.uuid4())[:8]
        if self._mock:
            logger.info(f"[SLACK-MOCK] Channel: {channel} | id={delivery_id}")
            _DISPATCH_LOG.append({
                "channel": "slack", "slack_channel": channel,
                "body_preview": text[:100], "delivery_id": delivery_id,
                "thread_id": thread_id, "timestamp": now_iso(), "status": "simulated",
            })
            return {"status": "simulated", "delivery_id": delivery_id, "channel": "slack"}
        return {"status": "sent", "delivery_id": delivery_id, "channel": "slack"}


class TeamsAdapter:
    """Mock Microsoft Teams webhook adapter."""

    def __init__(self, config: Dict[str, Any]):
        self._mock = str(config.get("mock_mode", "true")).lower() == "true"
        self._webhook_url = config.get("teams_webhook_url", "")

    def send(self, title: str, text: str,
             thread_id: Optional[str] = None) -> Dict[str, Any]:
        delivery_id = str(uuid.uuid4())[:8]
        if self._mock:
            logger.info(f"[TEAMS-MOCK] Title: {title[:40]} | id={delivery_id}")
            _DISPATCH_LOG.append({
                "channel": "teams", "title": title,
                "body_preview": text[:100], "delivery_id": delivery_id,
                "thread_id": thread_id, "timestamp": now_iso(), "status": "simulated",
            })
            return {"status": "simulated", "delivery_id": delivery_id, "channel": "teams"}
        return {"status": "sent", "delivery_id": delivery_id, "channel": "teams"}


class ChatAdapter:
    """Mock chat (websocket/REST) adapter."""

    def __init__(self, config: Dict[str, Any]):
        self._mock = str(config.get("mock_mode", "true")).lower() == "true"
        self._api_url = config.get("chat_api_url", "")

    def send(self, session_id: str, text: str,
             thread_id: Optional[str] = None) -> Dict[str, Any]:
        delivery_id = str(uuid.uuid4())[:8]
        if self._mock:
            logger.info(f"[CHAT-MOCK] Session: {session_id} | id={delivery_id}")
            _DISPATCH_LOG.append({
                "channel": "chat", "session_id": session_id,
                "body_preview": text[:100], "delivery_id": delivery_id,
                "thread_id": thread_id, "timestamp": now_iso(), "status": "simulated",
            })
            return {"status": "simulated", "delivery_id": delivery_id, "channel": "chat"}
        return {"status": "sent", "delivery_id": delivery_id, "channel": "chat"}


class APICallbackAdapter:
    """Mock REST callback / webhook adapter."""

    def __init__(self, config: Dict[str, Any]):
        self._mock = str(config.get("mock_mode", "true")).lower() == "true"
        self._callback_url = config.get("api_callback_url", "")

    def send(self, payload: Dict[str, Any],
             thread_id: Optional[str] = None) -> Dict[str, Any]:
        delivery_id = str(uuid.uuid4())[:8]
        if self._mock:
            logger.info(f"[API-MOCK] Callback payload | id={delivery_id}")
            _DISPATCH_LOG.append({
                "channel": "api", "payload_preview": str(payload)[:100],
                "delivery_id": delivery_id, "thread_id": thread_id,
                "timestamp": now_iso(), "status": "simulated",
            })
            return {"status": "simulated", "delivery_id": delivery_id, "channel": "api"}
        return {"status": "sent", "delivery_id": delivery_id, "channel": "api"}


class MemoAdapter:
    """Formal memo -- saves to file/store."""

    def __init__(self, config: Dict[str, Any]):
        self._mock = str(config.get("mock_mode", "true")).lower() == "true"

    def send(self, title: str, text: str,
             thread_id: Optional[str] = None) -> Dict[str, Any]:
        delivery_id = str(uuid.uuid4())[:8]
        if self._mock:
            logger.info(f"[MEMO-MOCK] Title: {title[:40]} | id={delivery_id}")
            _DISPATCH_LOG.append({
                "channel": "memo", "title": title,
                "body_preview": text[:200], "delivery_id": delivery_id,
                "thread_id": thread_id, "timestamp": now_iso(), "status": "simulated",
            })
            return {"status": "simulated", "delivery_id": delivery_id, "channel": "memo"}
        return {"status": "saved", "delivery_id": delivery_id, "channel": "memo"}


# ---------------------------------------------------------------------------
# Channel Dispatcher
# ---------------------------------------------------------------------------

class ChannelDispatcher:
    """
    Routes a finalised response to the correct channel adapter.
    Config-driven: adapters are initialised from the consumer config dict.
    """

    def __init__(self, channels_config: Dict[str, Any]):
        self._cfg = channels_config
        mock = channels_config.get("mock_mode", "true")
        cfg_with_mock = {**channels_config, "mock_mode": mock}
        self._adapters = {
            "email": EmailAdapter(cfg_with_mock),
            "chat":  ChatAdapter(cfg_with_mock),
            "slack": SlackAdapter(cfg_with_mock),
            "teams": TeamsAdapter(cfg_with_mock),
            "api":   APICallbackAdapter(cfg_with_mock),
            "memo":  MemoAdapter(cfg_with_mock),
        }

    def dispatch(self, channel: str, content: str, metadata: Dict[str, Any],
                 thread_id: Optional[str] = None) -> Dict[str, Any]:
        channel = channel.lower()
        adapter = self._adapters.get(channel)
        if not adapter:
            logger.warning(f"No adapter for channel '{channel}'. Using API fallback.")
            adapter = self._adapters["api"]

        try:
            if channel == "email":
                return adapter.send(
                    to=metadata.get("sender_email", metadata.get("sender", "unknown@example.com")),
                    subject=f"Re: {metadata.get('subject', 'Your enquiry')}",
                    body=content, thread_id=thread_id,
                )
            elif channel == "slack":
                return adapter.send(
                    channel=metadata.get("slack_channel", self._cfg.get("slack_channel", "#general")),
                    text=content, thread_id=thread_id,
                )
            elif channel == "teams":
                return adapter.send(
                    title=metadata.get("subject", "Communication Update"),
                    text=content, thread_id=thread_id,
                )
            elif channel == "chat":
                return adapter.send(
                    session_id=metadata.get("session_id", "unknown"),
                    text=content, thread_id=thread_id,
                )
            elif channel == "memo":
                return adapter.send(
                    title=metadata.get("subject", "Internal Memo"),
                    text=content, thread_id=thread_id,
                )
            else:
                return adapter.send(
                    payload={"content": content, "metadata": metadata},
                    thread_id=thread_id,
                )
        except Exception as exc:
            logger.error(f"Dispatch to {channel} failed: {exc}")
            return {"status": "failed", "channel": channel, "error": str(exc)}

    @staticmethod
    def get_dispatch_log() -> List[Dict[str, Any]]:
        return list(_DISPATCH_LOG)


# ---------------------------------------------------------------------------
# CRM Logger
# ---------------------------------------------------------------------------

class CRMLogTool:
    """Logs full interaction threads to CRM. Mock: in-memory list."""

    def log(self, thread_id: str, session_id: str, workflow: str,
            channel: str, classification: str, resolution: str,
            history: List[Dict[str, Any]]) -> Dict[str, Any]:
        crm_id = str(uuid.uuid4())
        entry = {
            "crm_id": crm_id,
            "thread_id": thread_id,
            "session_id": session_id,
            "workflow": workflow,
            "channel": channel,
            "classification": classification,
            "resolution_summary": resolution[:200],
            "interaction_count": len(history),
            "timestamp": now_iso(),
        }
        _CRM_LOG.append(entry)
        logger.info(f"[CRM] Logged thread {thread_id} | crm_id={crm_id[:8]}")
        return {"success": True, "crm_id": crm_id}

    @staticmethod
    def get_log() -> List[Dict[str, Any]]:
        return list(_CRM_LOG)


# ---------------------------------------------------------------------------
# Audit Tool
# ---------------------------------------------------------------------------

_AUDIT_LOG: List[Dict[str, Any]] = []


class AuditLogTool:
    def log(self, event_type: str, workflow: str, session_id: str,
            channels: List[str], details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        audit_id = str(uuid.uuid4())
        entry = {
            "audit_id": audit_id,
            "event_type": event_type,
            "workflow": workflow,
            "session_id": session_id,
            "channels": channels,
            "details": details or {},
            "timestamp": now_iso(),
        }
        _AUDIT_LOG.append(entry)
        logger.info(f"[AUDIT] {event_type} | session={session_id} | id={audit_id[:8]}")
        return {"success": True, "audit_id": audit_id}

    @staticmethod
    def get_log() -> List[Dict[str, Any]]:
        return list(_AUDIT_LOG)
