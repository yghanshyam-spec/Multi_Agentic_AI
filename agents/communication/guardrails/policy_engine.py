"""
communication/guardrails/policy_engine.py
Input safety, PII detection, and content policy enforcement.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)

_PII_PATTERNS = [
    re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b"),
    re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b"),  # credit card
]


class GuardrailEngine:
    def __init__(self, config: Dict[str, Any]):
        gr = config.get("guardrails", {})
        self._max_len     = gr.get("max_input_length", 10000)
        self._pii_detect  = gr.get("pii_detection", True)
        self._block_pii   = gr.get("block_on_pii", False)
        self._profanity   = gr.get("profanity_filter", False)

    def check_input(self, text: str) -> Tuple[bool, List[str]]:
        issues = []
        if len(text) > self._max_len:
            issues.append(f"Input exceeds {self._max_len} character limit")
        if self._pii_detect:
            for pat in _PII_PATTERNS:
                if pat.search(text):
                    issues.append("PII detected in input (email/phone/card)")
                    break
        blocked = self._block_pii and any("PII" in i for i in issues)
        return not blocked, issues

    def validate_channel(self, channel: str, allowed_channels: List[str]) -> Tuple[bool, str]:
        if channel.lower() not in [c.lower() for c in allowed_channels]:
            return False, f"Channel '{channel}' not in allowed list: {allowed_channels}"
        return True, ""
