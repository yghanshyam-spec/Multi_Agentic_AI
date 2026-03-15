"""
agents/salesforce/observability/langfuse_client.py
================================================
Observability wrapper for the Salesforce agent.

All tracing and prompt management is delegated to shared/langfuse_manager.py.
This file exists as the standard per-agent observability extension point.

Usage
-----
    from agents.salesforce.observability.langfuse_client import get_agent_tracer
    tracer = get_agent_tracer()
    with tracer.trace("my_workflow", session_id=sid, input=raw_input):
        ...
"""
from __future__ import annotations
from shared.langfuse_manager import get_tracer, AgentTracer


def get_agent_tracer() -> AgentTracer:
    """Return an AgentTracer scoped to the Salesforce agent."""
    return get_tracer("salesforce_agent")
