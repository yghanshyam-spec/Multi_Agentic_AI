"""
agents/router/observability/langfuse_client.py
================================================
Thin shim kept for backward compatibility.

All tracing is handled exclusively by shared.langfuse_manager — this module
simply re-exports get_tracer under a legacy name so any existing code that
imported get_agent_tracer() continues to work without modification.

New code should import directly from shared.langfuse_manager or shared.common.
"""
from __future__ import annotations
from shared.langfuse_manager import get_tracer, AgentTracer  # noqa: F401


def get_agent_tracer() -> AgentTracer:
    """Return an AgentTracer scoped to the Router agent."""
    return get_tracer("router_agent")


__all__ = ["get_agent_tracer", "get_tracer", "AgentTracer"]
