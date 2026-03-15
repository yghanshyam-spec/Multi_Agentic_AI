"""
agents/router/tools/load_monitor.py
=====================================
Load-monitoring tool for the Router Agent.
Queries per-agent queue depths and health status.
Mock implementation — swap in your real metrics API (Prometheus, Datadog, etc.)
in production.
"""
from __future__ import annotations

from typing import Any, Dict, List


AGENT_REGISTRY: List[str] = [
    "INTENT_AGENT", "PLANNER_AGENT", "WORKFLOW_AGENT",
    "REASONING_AGENT", "GENERATOR_AGENT", "COMMUNICATION_AGENT",
    "EXECUTION_AGENT", "HITL_AGENT", "AUDIT_AGENT",
]


class LoadMonitor:
    """
    Provides real-time load metrics for each agent.

    Production: replace _fetch_metrics() with calls to your observability stack.
    """

    def get_metrics(self, agents: List[str] = None) -> Dict[str, Dict[str, Any]]:
        targets = agents or AGENT_REGISTRY
        return {agent: self._fetch_metrics(agent) for agent in targets}

    def _fetch_metrics(self, agent: str) -> Dict[str, Any]:
        # Mock: all agents healthy with zero queue depth
        return {
            "queue_depth":   0,
            "avg_latency_ms": 120,
            "status":        "healthy",
            "last_checked":  None,
        }

    def is_agent_available(self, agent: str) -> bool:
        m = self._fetch_metrics(agent)
        return m["status"] == "healthy" and m["queue_depth"] < 100
