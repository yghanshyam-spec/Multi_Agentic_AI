"""
shared/utils/logger.py
=======================
Centralised logging factory for the entire accelerator.

All agents call get_logger(__name__) — never configure logging locally.

Usage
-----
    from shared.common import get_logger
    logger = get_logger(__name__)
    logger.info("Node started", extra={"node": "classify_intent_node"})

Environment
-----------
    LOG_LEVEL   — DEBUG | INFO | WARNING | ERROR  (default: INFO)
    APP_ENV     — development | production         (affects formatter)
"""
from __future__ import annotations

import logging
import os
import sys

# ── Colour codes (dev only) ───────────────────────────────────────────────────
_RESET  = "\033[0m"
_GREY   = "\033[90m"
_CYAN   = "\033[96m"
_YELLOW = "\033[93m"
_RED    = "\033[91m"
_BOLD   = "\033[1m"

_LEVEL_COLOURS = {
    logging.DEBUG:    _GREY,
    logging.INFO:     _CYAN,
    logging.WARNING:  _YELLOW,
    logging.ERROR:    _RED,
    logging.CRITICAL: _BOLD + _RED,
}


class _ColourFormatter(logging.Formatter):
    """Coloured formatter for development environments."""

    FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    def format(self, record: logging.LogRecord) -> str:
        colour = _LEVEL_COLOURS.get(record.levelno, "")
        formatter = logging.Formatter(
            fmt=f"{colour}{self.FMT}{_RESET}",
            datefmt="%H:%M:%S",
        )
        return formatter.format(record)


class _JsonFormatter(logging.Formatter):
    """Structured JSON formatter for production / log-aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        from shared.state import utc_now  # lazy import to avoid circular

        payload = {
            "ts":      utc_now(),
            "level":   record.levelname,
            "logger":  record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Merge any extra fields (e.g. node=, session_id=)
        for key, val in record.__dict__.items():
            if key not in (
                "msg", "args", "levelname", "levelno", "pathname", "filename",
                "module", "exc_info", "exc_text", "stack_info", "lineno",
                "funcName", "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process", "name", "message",
                "asctime",
            ):
                payload[key] = val
        return json.dumps(payload, default=str)


_configured_loggers: dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    """
    Return a configured logger for *name*.

    Loggers are cached — calling get_logger with the same name twice
    returns the same instance.
    """
    if name in _configured_loggers:
        return _configured_loggers[name]

    logger = logging.getLogger(name)

    # Only configure if no handlers already attached (avoids duplicate output)
    if not logger.handlers:
        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_str, logging.INFO)
        logger.setLevel(level)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        env = os.getenv("APP_ENV", "development").lower()
        if env == "production":
            handler.setFormatter(_JsonFormatter())
        else:
            handler.setFormatter(_ColourFormatter())

        logger.addHandler(handler)
        logger.propagate = False

    _configured_loggers[name] = logger
    return logger
