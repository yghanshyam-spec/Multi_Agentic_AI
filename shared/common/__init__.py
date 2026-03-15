"""
shared/common/__init__.py
==========================
Common package — single stable import namespace for all agents.

All 21 agents should import shared infrastructure ONLY from this package:

    from shared.common import get_llm, call_llm
    from shared.common import get_tracer, get_prompt, log_llm_call
    from shared.common import make_base_state, make_audit_event, build_trace_entry
    from shared.common import get_logger, retry

This consolidates:
  - LLM factory          → shared/llm_factory.py
  - Langfuse manager     → shared/langfuse_manager.py
  - State contracts      → shared/state.py
  - Core utilities       → shared/utils.py
  - Logger               → shared/utils/logger.py
  - Helpers              → shared/utils/helpers.py
  - Decorators           → shared/utils/decorators.py
"""
from shared.llm_factory import get_llm, call_llm, MockLLM, get_last_token_usage
from shared.agents.base_agent import BaseAgent
from shared.langfuse_manager import (
    get_tracer, get_langfuse, get_prompt, log_llm_call,
    traced_node, AgentTracer,
)
from shared.state import (
    BaseAgentState, AgentMessage, AgentResponse, AuditEvent, ExecutionMetadata,
    AgentType, AgentIntent, ExecutionStatus, Priority, HITLDecision,
    make_base_state, build_agent_response, make_audit_event, make_message,
    utc_now, new_id,
    SchedulerAgentState, IntentAgentState, PlannerAgentState,
    WorkflowAgentState, ReasoningAgentState, GeneratorAgentState,
    CommunicationAgentState, ExecutionAgentState, HITLAgentState, AuditAgentState,
)
from shared.utils import build_trace_entry, truncate_history, safe_get, timed_node
from shared.utils.logger import get_logger
from shared.utils.helpers import (
    truncate_text, extract_json_block, merge_dicts,
    format_duration, sanitize_log_value,
)
from shared.utils.decorators import retry, log_call, with_timeout

__all__ = [
    # LLM
    "get_llm", "call_llm", "MockLLM", "get_last_token_usage",
    # Shared base agent
    "BaseAgent",
    # Langfuse / observability
    "get_tracer", "get_langfuse", "get_prompt", "log_llm_call",
    "traced_node", "AgentTracer",
    # State contracts
    "BaseAgentState", "AgentMessage", "AgentResponse", "AuditEvent",
    "AgentType", "AgentIntent", "ExecutionStatus", "Priority", "HITLDecision",
    "make_base_state", "build_agent_response", "make_audit_event", "make_message",
    "utc_now", "new_id",
    "SchedulerAgentState", "IntentAgentState", "PlannerAgentState",
    "WorkflowAgentState", "ReasoningAgentState", "GeneratorAgentState",
    "CommunicationAgentState", "ExecutionAgentState", "HITLAgentState", "AuditAgentState",
    # Utilities
    "build_trace_entry", "truncate_history", "safe_get", "timed_node",
    "get_logger", "truncate_text", "extract_json_block", "merge_dicts",
    "format_duration", "sanitize_log_value",
    "retry", "log_call", "with_timeout",
]
