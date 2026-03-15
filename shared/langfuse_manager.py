"""
shared/langfuse_manager.py
===========================
Centralised Langfuse observability layer — **Langfuse SDK v3 compatible**.

Public interface (unchanged — no agent code needs editing):
  get_tracer(agent_name)          -> AgentTracer
  log_llm_call(agent, node, ...)  -> None
  get_prompt(key, *, ...)         -> str
  traced_node(agent, node)        -> decorator
  reset_client()                  -> None

Langfuse v3 removed the low-level lf.trace() / lf.span() / lf.generation()
calls.  This module now uses the official v3 approach:

  • @observe decorator wraps each node/workflow function automatically.
  • langfuse_context.update_current_trace()       sets trace-level metadata.
  • langfuse_context.update_current_observation() sets span/generation metadata.
  • langfuse_context.flush()                      ships all pending events.

Object hierarchy produced on the Langfuse UI:
  Trace  (one per agent run — set by tracer.trace() context manager)
    └─ Span / Generation  (one per LangGraph node — set by @traced_node or
                           by log_llm_call inside the node)

Environment variables (.env at project root):
  LANGFUSE_PUBLIC_KEY   — project public key
  LANGFUSE_SECRET_KEY   — project secret key
  LANGFUSE_HOST         — optional, default https://cloud.langfuse.com
  LANGFUSE_ENABLED      — "true" / "false"  (default: auto-detect from keys)
"""
from __future__ import annotations

import functools
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from dotenv import load_dotenv

# ── Load root .env once ───────────────────────────────────────────────────────
_ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"
if _ROOT_ENV.exists():
    load_dotenv(_ROOT_ENV, override=False)


# ── Try to import Langfuse v3 SDK ─────────────────────────────────────────────
_LANGFUSE_SDK_AVAILABLE = False
_observe = None
_langfuse_context = None
_LangfuseClient = None

# try:
#     from langfuse.decorators import observe as _observe_import
#     from langfuse.decorators import langfuse_context as _langfuse_context_import
#     from langfuse import Langfuse as _LangfuseClientImport
#     _observe = _observe_import
#     _langfuse_context = _langfuse_context_import
#     _LangfuseClient = _LangfuseClientImport
#     _LANGFUSE_SDK_AVAILABLE = True
# except ImportError:
#     pass


# ── Singleton Langfuse client (only for get_prompt / auth_check / flush) ──────
_INSTANCE: Optional[Any] = None

# ── Prompt cache: only caches hits (misses are never cached) ──────────────────
_PROMPT_CACHE: Dict[str, str] = {}

# ── Active tracer registry: agent_name → AgentTracer ─────────────────────────
_TRACER_REGISTRY: Dict[str, "AgentTracer"] = {}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _is_enabled() -> bool:
    """Read LANGFUSE_ENABLED from env at call-time (not cached)."""
    explicit = os.getenv("LANGFUSE_ENABLED", "").strip().lower()
    if explicit == "false":
        return False
    if explicit == "true":
        return True
    return (bool(os.getenv("LANGFUSE_PUBLIC_KEY", "").strip()) and
            bool(os.getenv("LANGFUSE_SECRET_KEY", "").strip()))


def _get_client() -> Optional[Any]:
    """Return cached Langfuse client or None."""
    global _INSTANCE
    if not _is_enabled() or not _LANGFUSE_SDK_AVAILABLE:
        return None
    if _INSTANCE is not None:
        return _INSTANCE
    try:
        _INSTANCE = _LangfuseClient(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "").strip(),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY", "").strip(),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").strip(),
        )
        return _INSTANCE
    except Exception as exc:
        print(f"[LangfuseManager] Init failed: {exc}")
        return None


def reset_client() -> None:
    """Force re-initialisation (call after .env reload)."""
    global _INSTANCE
    _INSTANCE = None
    _PROMPT_CACHE.clear()


def _safe_serialize(obj: Any) -> Any:
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _safe_serialize(v) for k, v in list(obj.items())[:50]}
    if isinstance(obj, (list, tuple)):
        return [_safe_serialize(i) for i in list(obj)[:50]]
    try:
        return str(obj)[:500]
    except Exception:
        return "<unserializable>"


def _normalise_usage(token_usage: dict | None) -> dict:
    if not token_usage:
        return {}
    out = {}
    for k, v in token_usage.items():
        try:
            out[k] = int(v)
        except (TypeError, ValueError):
            pass
    return out


class _SafeFormatMap(dict):
    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


# ─────────────────────────────────────────────────────────────────────────────
# NO-OP OBJECTS (Langfuse disabled or SDK not installed)
# ─────────────────────────────────────────────────────────────────────────────

class _NoOpCtx:
    """Null-object returned by AgentTracer.trace() when tracing is off."""
    id: str = ""
    def update(self, **kwargs): pass
    def __enter__(self): return self
    def __exit__(self, *_): pass


# ─────────────────────────────────────────────────────────────────────────────
# AGENT TRACER  — public façade used by all run_*() entry-points
# ─────────────────────────────────────────────────────────────────────────────

class AgentTracer:
    """
    Per-agent tracer.  Obtained via ``get_tracer("agent_name")``.

    Usage in run_*() entry-points::

        tracer = get_tracer("reasoning_agent")
        with tracer.trace("reasoning_workflow", session_id=sid, input=raw_input):
            state = frame_problem_node(state)
            ...
        tracer.flush()
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        # Track the trace-level context we want to stamp on the current observation
        self._trace_meta: dict = {}

    @contextmanager
    def trace(
        self,
        workflow: str,
        session_id: str = "",
        input: Any = None,
        metadata: dict | None = None,
    ):
        """
        Context manager that:
        1. Registers this tracer in _TRACER_REGISTRY so log_llm_call() can
           find it from inside node functions.
        2. When Langfuse is enabled, wraps the block with @observe so that
           all @traced_node calls inside become child spans of the same trace.
        3. Stamps trace-level metadata (name, session_id, input) via
           langfuse_context.update_current_trace() immediately after entry.
        """
        # print(f"[AgentTracer] Starting trace for workflow '{workflow}' (agent='{self.agent_name}', session_id='{session_id}')...")
        self._trace_meta = {
            "name": f"{self.agent_name}.{workflow}",
            "session_id": session_id or None,
            "input": _safe_serialize(input),
            "metadata": metadata or {"agent": self.agent_name},
        }
        _TRACER_REGISTRY[self.agent_name] = self

        if not _is_enabled() or not _LANGFUSE_SDK_AVAILABLE:
            try:
                yield _NoOpCtx()
            finally:
                _TRACER_REGISTRY.pop(self.agent_name, None)
                self._trace_meta = {}
            return

        # Wrap the entire block in an @observe call so all child @observe calls
        # (from @traced_node / log_llm_call) nest under this trace.
        @_observe(name=f"{self.agent_name}.{workflow}", capture_input=False, capture_output=False)
        def _run_traced_block(runner_fn):
            # Stamp trace-level fields immediately
            try:
                _langfuse_context.update_current_trace(
                    name=self._trace_meta["name"],
                    session_id=self._trace_meta["session_id"],
                    input=self._trace_meta["input"],
                    metadata=self._trace_meta["metadata"],
                )
            except Exception:
                pass
            return runner_fn()

        result_holder = {}
        exc_holder = {}

        def _body():
            result_holder["ctx"] = _NoOpCtx()
            result_holder["ctx"].id = _langfuse_context.get_current_trace_id() or ""
            return result_holder["ctx"]

        try:
            _run_traced_block(_body)
            yield result_holder.get("ctx", _NoOpCtx())
        except Exception as exc:
            exc_holder["exc"] = exc
            # Mark the trace as errored
            try:
                _langfuse_context.update_current_trace(
                    metadata={"error": str(exc)[:300]}
                )
            except Exception:
                pass
            raise
        finally:
            _TRACER_REGISTRY.pop(self.agent_name, None)
            self._trace_meta = {}
            try:
                _langfuse_context.flush()
            except Exception:
                pass

    def flush(self) -> None:
        """Explicit flush — safe to call even when tracing is off."""
        if not _is_enabled() or not _LANGFUSE_SDK_AVAILABLE:
            return
        try:
            _langfuse_context.flush()
        except Exception:
            pass
        lf = _get_client()
        if lf:
            try:
                lf.flush()
            except Exception:
                pass

    def _stamp_observation(
        self,
        node_name: str,
        model: str | None = None,
        prompt: str | None = None,
        completion: str | None = None,
        token_usage: dict | None = None,
        duration_ms: int | None = None,
        level: str = "DEFAULT",
    ) -> None:
        """
        Update the *current* observation (span or generation) with metadata.
        Called from inside an @observe-decorated function so there is always
        a current observation in context.
        """
        if not _is_enabled() or not _LANGFUSE_SDK_AVAILABLE:
            return
        try:
            kwargs: dict = {"name": node_name, "level": level}
            if prompt is not None:
                kwargs["input"] = [{"role": "user", "content": str(prompt)[:4000]}]
            if completion is not None:
                kwargs["output"] = str(completion)[:4000]
            if model is not None:
                kwargs["model"] = model
            if token_usage:
                kwargs["usage"] = _normalise_usage(token_usage)
            if duration_ms is not None:
                kwargs["metadata"] = {"duration_ms": duration_ms}
            _langfuse_context.update_current_observation(**kwargs)
        except Exception:
            pass


def get_tracer(agent_name: str = "accelerator") -> AgentTracer:
    """Factory — returns an AgentTracer scoped to *agent_name*."""
    return AgentTracer(agent_name)


# ─────────────────────────────────────────────────────────────────────────────
# TRACED NODE DECORATOR
# ─────────────────────────────────────────────────────────────────────────────

def traced_node(agent_name: str, node_name: str):
    """
    Decorator for LangGraph node functions.

    When Langfuse is enabled, wraps the node in an @observe span that is
    automatically nested under the active trace for *agent_name*.
    No-op when Langfuse is disabled::

        @traced_node("reasoning_agent", "frame_problem_node")
        def frame_problem_node(state: dict) -> dict:
            ...
    """
    def decorator(fn: Callable) -> Callable:
        if not _LANGFUSE_SDK_AVAILABLE:
            return fn  # zero overhead when SDK missing

        @_observe(name=node_name, capture_input=False, capture_output=False)
        @functools.wraps(fn)
        def _observed(state: dict, *args, **kwargs) -> dict:
            t0 = time.monotonic()
            try:
                result = fn(state, *args, **kwargs)
                duration_ms = int((time.monotonic() - t0) * 1000)
                tracer = _TRACER_REGISTRY.get(agent_name)
                if tracer:
                    tracer._stamp_observation(
                        node_name=node_name,
                        duration_ms=duration_ms,
                    )
                return result
            except Exception as exc:
                if _is_enabled():
                    try:
                        _langfuse_context.update_current_observation(
                            name=node_name,
                            level="ERROR",
                            metadata={"error": str(exc)[:300]},
                        )
                    except Exception:
                        pass
                raise

        @functools.wraps(fn)
        def wrapper(state: dict, *args, **kwargs) -> dict:
            if not _is_enabled():
                return fn(state, *args, **kwargs)
            return _observed(state, *args, **kwargs)

        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# log_llm_call  — module-level convenience used by every node
# ─────────────────────────────────────────────────────────────────────────────

def log_llm_call(
    agent_name: str,
    node_name: str,
    model: str,
    prompt: str,
    response: str,
    session_id: str = "",
    token_usage: dict | None = None,
) -> None:
    """
    Log a single LLM call as a Langfuse generation nested under the current
    active trace.

    Call this immediately after every call_llm() in node functions::

        result = call_llm(llm, sys_p, user_p, node_hint="frame_problem")
        log_llm_call("reasoning_agent", "frame_problem_node",
                     os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                     sys_p[:300], str(result),
                     state.get("session_id", ""),
                     token_usage=get_last_token_usage())
    """
    if not _is_enabled() or not _LANGFUSE_SDK_AVAILABLE:
        return

    tracer = _TRACER_REGISTRY.get(agent_name)

    if tracer is not None:
        # We are inside a tracer.trace() block — stamp the *current* observation
        # (which was opened by @traced_node, or is the trace itself if called
        # outside a @traced_node wrapper).
        tracer._stamp_observation(
            node_name=node_name,
            model=model,
            prompt=prompt,
            completion=response,
            token_usage=token_usage,
        )
    else:
        # Fallback: no active trace context — create a standalone generation
        # wrapped in its own @observe call so it at least appears in Langfuse.
        @_observe(name=node_name, as_type="generation",
                  capture_input=False, capture_output=False)
        def _standalone():
            try:
                _langfuse_context.update_current_observation(
                    name=node_name,
                    model=model,
                    input=[{"role": "user", "content": str(prompt)[:4000]}],
                    output=str(response)[:4000],
                    usage=_normalise_usage(token_usage),
                    metadata={"session_id": session_id, "agent": agent_name},
                )
                _langfuse_context.update_current_trace(
                    session_id=session_id or None,
                    metadata={"agent": agent_name},
                )
            except Exception:
                pass

        try:
            _standalone()
            _langfuse_context.flush()
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT REGISTRY
# ─────────────────────────────────────────────────────────────────────────────

def get_prompt(
    key: str,
    *,
    agent_name: str = "",
    fallback: str = "",
    langfuse_label: str = "production",
    **template_vars,
) -> str:
    """
    3-tier prompt resolution:
      1. Langfuse prompt registry  (fetched once and cached on hit)
      2. Consumer-supplied fallback string
      3. Empty string with a printed warning

    Template variables are substituted with str.format_map(); missing keys
    are preserved as literal ``{key}`` (never raise KeyError).
    """
    cache_key = f"{agent_name}:{key}"

    # print(f"[LangfuseManager] Fetching prompt '{key}' for agent '{agent_name}'...")
    # print(f"_PROMPT_CACHE.get- cache_key - {_PROMPT_CACHE.get(cache_key, '')}")

    # ── 1. Langfuse registry ──────────────────────────────────────────────────
    if cache_key not in _PROMPT_CACHE:
        lf = _get_client()
        if lf:
            try:
                lf_prompt = lf.get_prompt(key, label=langfuse_label)
                 
                text = lf_prompt.prompt if hasattr(lf_prompt, "prompt") else str(lf_prompt)
                if text:
                    # print(f"[LangfuseManager] Prompt cache {'HIT' if cache_key in _PROMPT_CACHE else 'MISS'} for '{key}' (agent='{agent_name}')")
                    # print(f"text-{text[:50]}")  # print start of text for visibility in logs, even when cache hit
                    _PROMPT_CACHE[cache_key] = text   # only cache hits
                else:
                    # print(f"fallback-{fallback[:50]}")  # print fallback for visibility in logs, even when cache miss
                    lf.create_prompt(
                        name=fallback,
                        type="chat",
                        prompt=key,
                        labels=["production"],
                        config={
                            "auto_created": True,
                            "prompt_key": key,
                        },
                    )
            except Exception:
                
                # print(f"[LangfuseManager] WARNING: Failed to fetch prompt '{key}' from Langfuse (agent='{agent_name}'). Using fallback. Exception: {Exception}")                
                # print(f"Exception-{Exception}")
                pass   # miss — will retry next call

    cached = _PROMPT_CACHE.get(cache_key, "")
    # print(f"_PROMPT_CACHE.get- cache_key - {_PROMPT_CACHE.get(cache_key, '')}") 
    # print(f"[LangfuseManager] Prompt cache {'HIT' if cache_key in _PROMPT_CACHE else 'MISS'} for '{key}' (agent='{agent_name}')")

    # ── 2. Pick template source ───────────────────────────────────────────────
    template = cached or fallback
    if not template:
        # print(f"[LangfuseManager] WARNING: No prompt found for '{key}' (agent={agent_name})")
        return ""

    # ── 3. Substitute variables ───────────────────────────────────────────────
    if template_vars:
        try:
            return template.format_map(_SafeFormatMap(template_vars))
        except Exception:
            return template
    return template


# ─────────────────────────────────────────────────────────────────────────────
# LEGACY ALIAS  (keeps any code that imports AgentTracer directly working)
# ─────────────────────────────────────────────────────────────────────────────
# AgentTracer is already defined above.

# ─────────────────────────────────────────────────────────────────────────────
# COMPATIBILITY ALIASES
# ─────────────────────────────────────────────────────────────────────────────
# get_langfuse() kept for any code that imported it directly (e.g. shared/__init__.py)
def get_langfuse():
    """Return the singleton Langfuse client (or None). Alias for _get_client()."""
    return _get_client()
