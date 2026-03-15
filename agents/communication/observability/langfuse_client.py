"""
communication/observability/langfuse_client.py
Langfuse tracing + prompt management. Degrades to no-op when keys absent.
"""
from __future__ import annotations

import os
import uuid
from typing import Any, Dict, Optional

from communication.utils.logger import get_logger

logger = get_logger(__name__)


class _NoOpSpan:
    span_id = "noop"
    def end(self, **kwargs): pass


class _NoOpTrace:
    trace_id = "noop"
    def update(self, **kwargs): pass


class LangfuseClient:
    def __init__(self, agent_config: Dict[str, Any]):
        obs = agent_config.get("observability", {})
        self._enabled = obs.get("langfuse_enabled", False)
        self._client = None
        if self._enabled:
            try:
                from langfuse import Langfuse  # type: ignore
                self._client = Langfuse(
                    public_key=os.environ.get("LANGFUSE_PUBLIC_KEY", ""),
                    secret_key=os.environ.get("LANGFUSE_SECRET_KEY", ""),
                    host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
                )
                logger.info("Langfuse client initialised")
            except Exception as exc:
                logger.warning(f"Langfuse init failed ({exc}). Tracing disabled.")
                self._enabled = False

    def start_trace(self, name: str, session_id: Optional[str] = None,
                    input: Optional[Dict] = None, metadata: Optional[Dict] = None,
                    trace_id: Optional[str] = None):
        if not self._enabled or not self._client:
            t = _NoOpTrace(); t.trace_id = trace_id or str(uuid.uuid4()); return t
        try:
            return self._client.trace(name=name, id=trace_id or str(uuid.uuid4()),
                                      session_id=session_id, input=input or {},
                                      metadata=metadata or {})
        except Exception as exc:
            logger.warning(f"start_trace failed: {exc}"); return _NoOpTrace()

    def end_trace(self, trace, output: Optional[Dict] = None, error: Optional[str] = None):
        if not self._enabled: return
        try: trace.update(output=output or {}, status_message=error or "")
        except Exception: pass

    def start_span(self, name: str, trace_id: Optional[str] = None,
                   input: Optional[Dict] = None):
        if not self._enabled or not self._client: return _NoOpSpan()
        try:
            return self._client.span(name=name, trace_id=trace_id, input=input or {})
        except Exception: return _NoOpSpan()

    def end_span(self, span, output: Optional[Dict] = None, error: Optional[str] = None):
        if not self._enabled: return
        try: span.end(output=output or {}, status_message=error or "")
        except Exception: pass

    def get_prompt(self, name: str, version: str = "latest") -> Optional[str]:
        if not self._enabled or not self._client: return None
        try:
            return self._client.get_prompt(name, version=version).prompt
        except Exception: return None

    def flush(self):
        if self._client:
            try: self._client.flush()
            except Exception: pass
