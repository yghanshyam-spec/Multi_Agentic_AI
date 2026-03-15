"""
communication/utils/helpers.py
General-purpose helpers: dates, strings, channel utilities.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def truncate(text: str, max_len: int = 300) -> str:
    return text if len(text) <= max_len else text[:max_len - 3] + "..."


def safe_get(obj: Any, *keys, default=None) -> Any:
    current = obj
    for key in keys:
        if current is None:
            return default
        current = current.get(key) if isinstance(current, dict) else getattr(current, key, None)
    return current if current is not None else default


def generate_thread_id(channel: str, sender: str, subject: str = "") -> str:
    raw = f"{channel}:{sender}:{subject}".lower().strip()
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def extract_email_address(text: str) -> Optional[str]:
    match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None


def channel_display_name(channel: str) -> str:
    return {
        "email": "Email",
        "chat": "Chat",
        "slack": "Slack",
        "teams": "Microsoft Teams",
        "api": "API / Webhook",
        "sms": "SMS",
        "voice": "Voice / Phone",
        "memo": "Formal Memo",
    }.get(channel.lower(), channel.title())


def word_count(text: str) -> int:
    return len(text.split())


def sentiment_hint(text: str) -> str:
    """Simple rule-based sentiment -- replaced by LLM in production."""
    text_lower = text.lower()
    negative_words = ["angry", "frustrated", "terrible", "awful", "unacceptable",
                      "complaint", "problem", "issue", "broken", "failed", "worst"]
    positive_words = ["thank", "great", "excellent", "happy", "pleased", "wonderful"]
    neg = sum(1 for w in negative_words if w in text_lower)
    pos = sum(1 for w in positive_words if w in text_lower)
    if neg > pos:
        return "negative"
    if pos > neg:
        return "positive"
    return "neutral"
