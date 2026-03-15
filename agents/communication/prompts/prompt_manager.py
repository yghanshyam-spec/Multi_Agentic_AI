"""
communication/prompts/prompt_manager.py
3-tier prompt resolution: Langfuse registry > local YAML > built-in defaults.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
# LangfuseClient replaced by shared.langfuse_manager
from shared.common import get_logger

logger = get_logger(__name__)

_BUILT_IN_DEFAULTS: Dict[str, str] = {
    # Channel detection & classification
    "comm_detect_channel": (
        "Analyse this inbound message payload and detect the communication channel. "
        "Return JSON: {{channel, sender, subject, body, timestamp, thread_id, raw_metadata}}\n"
        "Payload: {payload}"
    ),
    "comm_classify_message": (
        "Classify this communication message. Channel: {channel}. "
        "Message: {body}. Prior context summary: {context_summary}.\n"
        "Return JSON: {{classification (automated_response|human_escalation|acknowledgement_only), "
        "priority (low|medium|high|urgent), sentiment, topic, "
        "requires_human (bool), escalation_reason}}."
    ),
    "comm_draft_response": (
        "Draft a response for the following communication.\n"
        "Channel: {channel} (tone/length rules: {channel_rules})\n"
        "Classification: {classification}\n"
        "Original message: {body}\n"
        "Conversation history: {history}\n"
        "Talking points / instructions: {instructions}\n"
        "Draft a {tone} response appropriate for {channel}. "
        "Maximum length: {max_length} words."
    ),
    "comm_check_consistency": (
        "Review these draft responses across channels for factual contradictions.\n"
        "Drafts: {drafts}\n"
        "Prior communications in thread: {history}\n"
        "Return JSON: {{is_consistent (bool), contradictions (list of strings), "
        "suggested_fixes (list of strings), confidence}}."
    ),
    "comm_broadcast_draft": (
        "Draft a {channel} version of this internal communication.\n"
        "Talking points: {talking_points}\n"
        "Channel: {channel} ({channel_rules})\n"
        "Tone: {tone}. Max length: {max_length} words.\n"
        "Preserve all factual statements exactly. Adapt style only."
    ),
    "comm_summarise_context": (
        "Summarise this conversation thread in 2-3 sentences for context. "
        "Thread: {history}"
    ),
}


class PromptManager:
    def __init__(self, prompts_config: Dict[str, Any],
                 langfuse_client: Optional[object] = None  # unused: tracing via shared.langfuse_manager):
        self._config = prompts_config.get("prompts", prompts_config)
        self._langfuse = langfuse_client

    def get(self, key: str, **kwargs: Any) -> str:
        template = self._resolve(key)
        try:
            return template.format(**kwargs)
        except KeyError as exc:
            logger.warning(f"Prompt '{key}': missing placeholder {exc}")
            return template

    def _resolve(self, key: str) -> str:
        cfg = self._config.get(key, {})
        if isinstance(cfg, str):
            return cfg
        # 1. Langfuse
        if self._langfuse and isinstance(cfg, dict):
            remote = self._langfuse.get_prompt(cfg.get("langfuse_name", key),
                                               cfg.get("version", "latest"))
            if remote:
                return remote
        # 2. YAML fallback
        if isinstance(cfg, dict) and "fallback" in cfg:
            return cfg["fallback"]
        # 3. Built-in default
        if key in _BUILT_IN_DEFAULTS:
            return _BUILT_IN_DEFAULTS[key]
        logger.warning(f"No prompt found for '{key}'")
        return f"[PROMPT NOT FOUND: {key}]"
