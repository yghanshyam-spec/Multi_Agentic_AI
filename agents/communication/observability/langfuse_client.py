"""
agents/communication/observability/langfuse_client.py
===============================================
Backward-compatibility shim — delegates entirely to shared.langfuse_manager.

New code should import directly from shared.langfuse_manager or shared.common.
"""
from __future__ import annotations
from shared.langfuse_manager import get_tracer, AgentTracer  # noqa: F401


def get_agent_tracer() -> AgentTracer:
    """Return an AgentTracer scoped to the communication agent."""
    return get_tracer("communication_agent")


__all__ = ["get_agent_tracer", "get_tracer", "AgentTracer"]
