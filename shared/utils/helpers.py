"""
shared/utils/helpers.py
========================
String manipulation, date formatting, dict utilities, and other helpers.

All agents import from shared.common — never from this file directly.
"""
from __future__ import annotations

import json
import re
from typing import Any


def truncate_text(text: str, max_chars: int = 300, suffix: str = "…") -> str:
    """Truncate *text* to at most *max_chars* characters."""
    if not text or len(text) <= max_chars:
        return text or ""
    return text[:max_chars].rstrip() + suffix


def extract_json_block(text: str) -> dict:
    """
    Extract and parse the first JSON object or array from *text*.
    Falls back to the raw text wrapped in {"raw": ...} on failure.
    """
    # Strip markdown fences
    stripped = re.sub(r"```(?:json)?", "", text).strip("`").strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    # Try to find a {...} or [...] substring
    for pattern in (r"\{[\s\S]+\}", r"\[[\s\S]+\]"):
        m = re.search(pattern, stripped)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    return {"raw": text, "parsed": False}


def merge_dicts(*dicts: dict) -> dict:
    """
    Deep-merge an arbitrary number of dicts left-to-right.
    Later dicts override earlier ones; nested dicts are merged recursively.
    """
    result: dict = {}
    for d in dicts:
        if not isinstance(d, dict):
            continue
        for k, v in d.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = merge_dicts(result[k], v)
            else:
                result[k] = v
    return result


def format_duration(ms: int) -> str:
    """Human-readable duration: '2.3s', '450ms', '1m 3s'."""
    if ms < 1000:
        return f"{ms}ms"
    seconds = ms / 1000
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"


def sanitize_log_value(value: Any, max_len: int = 200) -> str:
    """
    Convert *value* to a safe, truncated string for logging.
    Redacts anything that looks like an API key or secret.
    """
    text = str(value)
    # Redact obvious secrets
    text = re.sub(r"(sk[-_][A-Za-z0-9]{10,})", "[REDACTED]", text)
    text = re.sub(r"(ANTHROPIC_API_KEY\s*=\s*)\S+", r"\1[REDACTED]", text)
    return truncate_text(text, max_len)
