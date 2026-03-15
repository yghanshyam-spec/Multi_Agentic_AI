"""
agents/generator/observability/langfuse_client.py
===================================================
Observability wrapper for the Generator agent.
All tracing is delegated to shared/langfuse_manager.py.
"""
from __future__ import annotations
from shared.langfuse_manager import get_tracer, AgentTracer

def get_agent_tracer() -> AgentTracer:
    """Return an AgentTracer scoped to the Generator agent."""
    return get_tracer("generator_agent")
