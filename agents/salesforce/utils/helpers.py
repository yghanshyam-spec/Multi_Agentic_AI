"""agents/salesforce/utils/helpers.py — agent-specific helper functions."""
from __future__ import annotations
from shared.common import truncate_text, merge_dicts, format_duration, sanitize_log_value

# Re-export shared helpers so agent code only needs to import from here
__all__ = ["truncate_text", "merge_dicts", "format_duration", "sanitize_log_value"]
