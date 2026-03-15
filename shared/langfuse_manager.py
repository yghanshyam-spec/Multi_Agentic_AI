"""
shared/langfuse_manager.py
===========================
Centralised Langfuse observability layer — **Langfuse SDK v4 compatible**.

Public interface (unchanged — no agent code needs editing):
  get_tracer(agent_name)          -> AgentTracer
  log_llm_call(agent, node, ...)  -> None
  get_prompt(key, *, ...)         -> str
  traced_node(agent, node)        -> decorator
  reset_client()                  -> None

Langfuse v4 is built on OpenTelemetry.  Key API changes from v2/v3:
  • langfuse.decorators removed  ->  use `from langfuse import observe, get_client`
  • lf.trace() / lf.span()       ->  get_client().start_as_current_observation()
  • update_current_trace()        ->  propagate_attributes() context manager
  • lf.get_prompt()               ->  get_client().get_prompt()
  • lf.create_prompt()            ->  get_client().create_prompt()

Object hierarchy produced on the Langfuse UI:
  Trace  (root span — one per agent run, opened by AgentTracer.trace())
    └─ Span / Generation  (one per LangGraph node — via traced_node / log_llm_call)

Environment variables (.env at project root):
  LANGFUSE_PUBLIC_KEY   — project public key  (pk-lf-...)
  LANGFUSE_SECRET_KEY   — project secret key  (sk-lf-...)
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


# ── Try to import Langfuse v4 SDK ─────────────────────────────────────────────
_LANGFUSE_SDK_AVAILABLE = False
_observe = None
_get_lf_client = None
_propagate_attributes = None

try:
    from langfuse import observe as _observe_import
    from langfuse import get_client as _get_client_import
    from langfuse import propagate_attributes as _propagate_attributes_import
    _observe = _observe_import
    _get_lf_client = _get_client_import
    _propagate_attributes = _propagate_attributes_import
    _LANGFUSE_SDK_AVAILABLE = True
except ImportError:
    pass


# ── Prompt cache: only caches hits ───────────────────────────────────────────
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
    return (
        bool(os.getenv("LANGFUSE_PUBLIC_KEY", "").strip()) and
        bool(os.getenv("LANGFUSE_SECRET_KEY", "").strip())
    )


def _get_client() -> Optional[Any]:
    """Return the Langfuse v4 singleton client or None."""
    if not _is_enabled() or not _LANGFUSE_SDK_AVAILABLE:
        return None
    try:
        # get_client() in v4 returns the singleton — initialises on first call
        return _get_lf_client()
    except Exception as exc:
        print(f"[LangfuseManager] Client init failed: {exc}")
        return None


def reset_client() -> None:
    """Clear prompt cache (call after .env reload)."""
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
# NO-OP OBJECTS  (Langfuse disabled or SDK not installed)
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

        tracer = get_tracer("communication_agent")
        with tracer.trace("omnichannel_response", session_id=sid, input=raw_input):
            result = graph.invoke(state)
        tracer.flush()
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    @contextmanager
    def trace(
        self,
        workflow: str,
        session_id: str = "",
        input: Any = None,
        metadata: dict | None = None,
    ):
        """
        Context manager that opens a root span (Langfuse trace) for the
        duration of the workflow.  All child observations created inside
        (via traced_node or log_llm_call) are automatically nested under it.
        """
        _TRACER_REGISTRY[self.agent_name] = self

        if not _is_enabled() or not _LANGFUSE_SDK_AVAILABLE:
            try:
                yield _NoOpCtx()
            finally:
                _TRACER_REGISTRY.pop(self.agent_name, None)
            return

        lf = _get_client()
        if lf is None:
            try:
                yield _NoOpCtx()
            finally:
                _TRACER_REGISTRY.pop(self.agent_name, None)
            return

        trace_name = f"{self.agent_name}.{workflow}"
        serialised_input = _safe_serialize(input)
        meta = metadata or {"agent": self.agent_name}

        try:
            # propagate_attributes stamps session_id + metadata onto every
            # child observation created inside this block (v4 replacement for
            # update_current_trace)
            with _propagate_attributes(
                session_id=session_id or None,
                metadata={k: str(v)[:200] for k, v in meta.items()},
            ):
                with lf.start_as_current_observation(
                    as_type="span",
                    name=trace_name,
                    input=serialised_input,
                ) as root_span:
                    ctx = _NoOpCtx()
                    try:
                        ctx.id = lf.get_current_trace_id() or ""
                    except Exception:
                        ctx.id = ""
                    try:
                        yield ctx
                    except Exception as exc:
                        try:
                            root_span.update(
                                metadata={"error": str(exc)[:300]}
                            )
                        except Exception:
                            pass
                        raise
        finally:
            _TRACER_REGISTRY.pop(self.agent_name, None)
            try:
                lf.flush()
            except Exception:
                pass

    def flush(self) -> None:
        """Explicit flush — safe to call even when tracing is off."""
        lf = _get_client()
        if lf:
            try:
                lf.flush()
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC FACTORY
# ─────────────────────────────────────────────────────────────────────────────

def get_tracer(agent_name: str = "accelerator") -> AgentTracer:
    """Return an AgentTracer scoped to *agent_name*."""
    return AgentTracer(agent_name)


# ─────────────────────────────────────────────────────────────────────────────
# TRACED NODE DECORATOR
# ─────────────────────────────────────────────────────────────────────────────

def traced_node(agent_name: str, node_name: str):
    """
    Decorator for LangGraph node functions.

    Wraps the node in a Langfuse span automatically nested under the active
    trace for *agent_name*.  No-op when Langfuse is disabled::

        @traced_node("communication_agent", "detect_channel_node")
        def detect_channel_node(state: dict) -> dict:
            ...
    """
    def decorator(fn: Callable) -> Callable:

        @functools.wraps(fn)
        def wrapper(state: dict, *args, **kwargs) -> dict:
            if not _is_enabled() or not _LANGFUSE_SDK_AVAILABLE:
                return fn(state, *args, **kwargs)

            lf = _get_client()
            if lf is None:
                return fn(state, *args, **kwargs)

            t0 = time.monotonic()
            try:
                with lf.start_as_current_observation(
                    as_type="span",
                    name=node_name,
                ) as span:
                    result = fn(state, *args, **kwargs)
                    duration_ms = int((time.monotonic() - t0) * 1000)
                    try:
                        span.update(metadata={"duration_ms": duration_ms})
                    except Exception:
                        pass
                    return result
            except Exception as exc:
                lf2 = _get_client()
                if lf2:
                    try:
                        with lf2.start_as_current_observation(
                            as_type="span", name=node_name
                        ) as err_span:
                            err_span.update(
                                metadata={"error": str(exc)[:300], "level": "ERROR"}
                            )
                    except Exception:
                        pass
                raise

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

        result = call_llm(llm, sys_p, user_p)
        log_llm_call(
            "communication_agent", "draft_response_node",
            os.getenv("LLM_MODEL", "gpt-4o"),
            sys_p, str(result),
            state.get("session_id", ""),
        )
    """
    if not _is_enabled() or not _LANGFUSE_SDK_AVAILABLE:
        return

    lf = _get_client()
    if lf is None:
        return

    try:
        with lf.start_as_current_observation(
            as_type="generation",
            name=node_name,
            model=model,
            input=[{"role": "user", "content": str(prompt)[:4000]}],
        ) as gen:
            gen.update(
                output=str(response)[:4000],
                usage=_normalise_usage(token_usage),
                metadata={"session_id": session_id, "agent": agent_name},
            )
    except Exception as exc:
        print(f"[LangfuseManager] log_llm_call failed for {node_name}: {exc}")


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
      2. Consumer-supplied fallback string (also auto-creates in Langfuse)
      3. Empty string with a warning

    Template variables are substituted with str.format_map(); missing keys
    are preserved as literal {key} — never raises KeyError.
    """
    cache_key = f"{agent_name}:{key}"

    # ── 1. Check local cache first ────────────────────────────────────────────
    if cache_key not in _PROMPT_CACHE:
        lf = _get_client()
        if lf:
            try:
                # v4: get_client().get_prompt(name, label=...)
                lf_prompt = lf.get_prompt(key, label=langfuse_label)
                text = (
                    lf_prompt.prompt
                    if hasattr(lf_prompt, "prompt")
                    else str(lf_prompt)
                )
                if text:
                    _PROMPT_CACHE[cache_key] = text
            except Exception:
                # Prompt does not exist in Langfuse — auto-create from fallback
                if fallback:
                    try:
                        lf.create_prompt(
                            name=key,        # identifier shown in Langfuse UI
                            type="text",
                            prompt=fallback, # the actual prompt body
                            labels=["production"],
                            config={"auto_created": True},
                        )
                        _PROMPT_CACHE[cache_key] = fallback
                        # print(f"[LangfuseManager] Auto-created prompt '{key}' in Langfuse.")
                    except Exception as create_exc:
                        print(f"[LangfuseManager] Could not auto-create prompt '{key}': {create_exc}")

    cached = _PROMPT_CACHE.get(cache_key, "")

    # ── 2. Pick template source ───────────────────────────────────────────────
    template = cached or fallback
    if not template:
        print(f"[LangfuseManager] WARNING: No prompt found for '{key}' (agent={agent_name})")
        return ""

    # ── 3. Substitute variables ───────────────────────────────────────────────
    if template_vars:
        try:
            return template.format_map(_SafeFormatMap(template_vars))
        except Exception:
            return template
    return template


# ─────────────────────────────────────────────────────────────────────────────
# COMPATIBILITY ALIASES
# ─────────────────────────────────────────────────────────────────────────────

def get_langfuse() -> Optional[Any]:
    """Return the Langfuse client singleton (or None)."""
    return _get_client()