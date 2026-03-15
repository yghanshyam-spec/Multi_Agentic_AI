"""
shared/__init__.py
==================
Top-level re-exports for the shared package.

Agents can import from either:
  - shared           (this file — backward compatible)
  - shared.common    (preferred — explicit, stable namespace)

Both resolve to the same implementations.
"""
from .state import (
    BaseAgentState, AgentMessage, AgentResponse, AuditEvent, ExecutionMetadata,
    AgentType, AgentIntent, ExecutionStatus, Priority, HITLDecision,
    make_base_state, build_agent_response, make_audit_event, make_message,
    utc_now, new_id,
    SchedulerAgentState, IntentAgentState, PlannerAgentState,
    WorkflowAgentState, ReasoningAgentState, GeneratorAgentState,
    CommunicationAgentState, ExecutionAgentState, HITLAgentState, AuditAgentState,
)
from .llm_factory import get_llm, call_llm, MockLLM
from .agents.base_agent import BaseAgent
from .utils import build_trace_entry, truncate_history, safe_get
from .langfuse_manager import (
    get_tracer, get_langfuse, get_prompt, log_llm_call,
    traced_node, AgentTracer,
)
