from __future__ import annotations

import functools
import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional, TypedDict, Union, Literal, Awaitable

# Core SDK
from git import List
from langfuse import (
    get_client,
    observe,
    propagate_attributes,
)

# Optional integrations (import lazily in helper methods to avoid hard deps):
# from langfuse.openai import openai, OpenAI, AsyncOpenAI, AzureOpenAI, AsyncAzureOpenAI
# from langfuse.langchain import CallbackHandler

# Types
ObservationType = Literal[
    "span",
    "generation",
    "agent",
    "tool",
    "chain",
    "retriever",
    "embedding",
    "evaluator",
    "guardrail",
]
ScoreType = Literal["NUMERIC", "BOOLEAN", "CATEGORICAL"]


class ChatMessageDict(TypedDict):
    role: str
    content: str


class ChatMessagePlaceholderDict(TypedDict):
    role: str
    content: str


class ChatMessageWithPlaceholdersDict_Message(TypedDict):
    type: Literal["message"]
    role: str
    content: str


class ChatMessageWithPlaceholdersDict_Placeholder(TypedDict):
    type: Literal["placeholder"]
    name: str


ChatMessageWithPlaceholdersDict = Union[
    ChatMessageWithPlaceholdersDict_Message,
    ChatMessageWithPlaceholdersDict_Placeholder,
]

@dataclass
class LangfuseConfig:
    """Optional config if you want to explicitly pass credentials instead of env vars."""
    public_key: Optional[str] = None
    secret_key: Optional[str] = None
    base_url: Optional[str] = None  # e.g., https://cloud.langfuse.com or https://us.cloud.langfuse.com
    environment: Optional[str] = None  # optional "env" tag on traces (dev/stage/prod)


class LangfuseWrapper:
    """
    All-in-one wrapper that exposes high-level methods covering:
      • Initialization (env or explicit config)
      • Function-level tracing (@observe) for sync & async
      • Context managers for spans & generations (nesting supported)
      • Global context propagation (user/session/tags/metadata)
      • Update current trace (tags/metadata/session/user/public/name)
      • Scoring/feedback (trace/span)
      • Prompt management (get/create/update + cache)
      • Datasets & experiments
      • OpenAI & LangChain integration helpers
      • Flush/auth/shutdown utilities
      • Helpers to link to an existing upstream trace via trace_context
    """

    def __init__(self, config: Optional[LangfuseConfig] = None):
        # Prefer environment variables: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL
        # get_client() reads env automatically, or you can pass explicit constructor via Langfuse(...)
        # We use get_client() here for simplicity.
        self.client = get_client()
        self.environment = config.environment if config else None

    # -------------------------------------------------------------------------
    # Observe (function-level decorator) — supports sync and async functions
    # -------------------------------------------------------------------------
    def observe_function(
        self,
        name: Optional[str] = None,
        as_type: Optional[ObservationType] = None,
        capture_input: Optional[bool] = None,
        capture_output: Optional[bool] = None,
        transform_to_string: Optional[Callable[[Iterable], str]] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Returns a decorator that wraps a function with Langfuse's @observe.
        It automatically captures input/output, timings, and errors, and nests within
        any active Langfuse/OTel context. Works for both sync and async functions.

        Args mirror Langfuse's @observe options.
        """
        # Create the base decorator from Langfuse
        base_decorator = observe(
            name=name,
            as_type=as_type,
            capture_input=capture_input,
            capture_output=capture_output,
            transform_to_string=transform_to_string,
        )

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            # apply Langfuse @observe first
            observed = base_decorator(func)

            # return observed function (no extra before/after unless you want to add custom logic)
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                return observed(*args, **kwargs)

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await observed(*args, **kwargs)

            return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

        return decorator
    
    # -------------------------------------------------------------------------
    # Context managers — spans/generations and arbitrary observation types
    # -------------------------------------------------------------------------
    def start_span(
        self,
        name: str,
        input: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        as_root: Optional[bool] = None,
        trace_context: Optional[Dict[str, str]] = None,  # { "trace_id": "...", "parent_span_id": "..." }
    ):
        """
        Start a span as the current observation (context manager).
        Children created inside will automatically nest here.
        """
        return self.client.start_as_current_observation(
            as_type="span",
            name=name,
            input=input,
            metadata=metadata,
            environment=self.environment,
            as_root=as_root,
            trace_context=trace_context,
        )

    def start_generation(
        self,
        name: str,
        model: Optional[str] = None,
        input: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        as_root: Optional[bool] = None,
        trace_context: Optional[Dict[str, str]] = None,
        model_parameters: Optional[Dict[str, Any]] = None,
    ):
        """
        Start a generation (LLM call) as the current observation.
        Automatically captures prompts, outputs, token usage, and cost when available.
        """
        return self.client.start_as_current_observation(
            as_type="generation",
            name=name,
            input=input,
            metadata=metadata,
            environment=self.environment,
            as_root=as_root,
            trace_context=trace_context,
            model=model,
            model_parameters=model_parameters,
        )

    def start_observation(
        self,
        as_type: ObservationType,
        name: str,
        **kwargs: Any,
    ):
        """
        Generic observation context manager for any supported type (agent, tool, chain, etc.).
        """
        return self.client.start_as_current_observation(
            as_type=as_type,
            name=name,
            environment=self.environment,
            **kwargs,
        )

    # -------------------------------------------------------------------------
    # Context propagation — user/session/tags/metadata applied to all children
    # -------------------------------------------------------------------------
    def propagate(
        self,
        *,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ):
        """
        Returns a context manager that propagates attributes to all observations created inside.
        Keep values small (<=200 chars) for metadata/tags to avoid drops.
        """
        return propagate_attributes(
            user_id=user_id,
            session_id=session_id,
            tags=tags,
            metadata=metadata,
        )

    # -------------------------------------------------------------------------
    # Update current trace (within active context)
    # -------------------------------------------------------------------------
    def update_current_trace(
        self,
        *,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        public: Optional[bool] = None,
    ):
        """
        Update attributes on the current trace (requires an active context/span).
        """
        return self.client.update_current_trace(
            user_id=user_id,
            session_id=session_id,
            tags=tags,
            metadata=metadata,
            name=name,
            public=public,
            environment=self.environment,
        )

    # -------------------------------------------------------------------------
    # Scores (feedback/evaluations)
    # -------------------------------------------------------------------------
    def score_current_span(
        self,
        name: str,
        value: Union[int, float, str],
        data_type: Optional[ScoreType] = None,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Score the current span/generation in context (NUMERIC/BOOLEAN/CATEGORICAL).
        """
        return self.client.score_current_span(
            name=name,
            value=value,
            data_type=data_type,
            comment=comment,
            metadata=metadata,
        )

    def score_current_trace(
        self,
        name: str,
        value: Union[int, float, str],
        data_type: Optional[ScoreType] = None,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Score the current trace in context.
        """
        return self.client.score_current_trace(
            name=name,
            value=value,
            data_type=data_type,
            comment=comment,
            metadata=metadata,
        )

    def create_score(
        self,
        *,
        name: str,
        value: Union[int, float, str],
        trace_id: Optional[str] = None,
        observation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        dataset_run_id: Optional[str] = None,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        data_type: Optional[ScoreType] = None,
        config_id: Optional[str] = None,
    ):
        """
        Create a score directly with explicit IDs (no active context needed).
        Useful for user feedback or external eval pipelines.
        """
        return self.client.create_score(
            name=name,
            value=value,
            trace_id=trace_id,
            observation_id=observation_id,
            session_id=session_id,
            dataset_run_id=dataset_run_id,
            comment=comment,
            metadata=metadata,
            data_type=data_type,
            config_id=config_id
            # environment=self.environment,
        )

    # -------------------------------------------------------------------------
    # Prompt management (client-side cache, retries, fallbacks)
    # -------------------------------------------------------------------------
    def get_prompt(self, name: str, label: Optional[str] = None,version: Optional[str] = None):
        return self.client.get_prompt(name=name, label=label, version=version)

    # def create_prompt(self, name: str, content: str, version: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
    #     return self.client.create_prompt(name=name, content=content, version=version, metadata=metadata)

    def create_prompt(self, name: str,  type: Optional[Literal["chat"]], prompt: List[Union[ChatMessageDict, ChatMessageWithPlaceholdersDict]], config: Optional[Any] = None, labels: List[str] = []):
        return self.client.create_prompt(name=name, type=type, prompt=prompt, config=config, labels=labels )


    def update_prompt(self, name: str, content: Optional[str] = None, version: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        return self.client.update_prompt(name=name, content=content, version=version, metadata=metadata)

    def clear_prompt_cache(self):
        return self.client.clear_prompt_cache()

    # -------------------------------------------------------------------------
    # Datasets & experiments (batch evaluation)
    # -------------------------------------------------------------------------
    def create_dataset(self, name: str, description: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        return self.client.create_dataset(name=name, description=description, metadata=metadata)

    def create_dataset_item(self, dataset_id: str, input: Any, expected_output: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None):
        return self.client.create_dataset_item(dataset_id=dataset_id, input=input, expected_output=expected_output, metadata=metadata)

    def run_experiment(
        self,
        name: str,
        dataset_id: str,
        evaluator: Callable[..., Any],
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Simple wrapper around the experiment runner (sync).
        """
        return self.client.run_experiment(
            name=name,
            dataset_id=dataset_id,
            evaluator=evaluator,
            description=description,
            metadata=metadata,
        )

    def run_batched_evaluation(
        self,
        dataset_id: str,
        evaluator: Callable[..., Any],
        batch_size: int = 32,
        resume_token: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        return self.client.run_batched_evaluation(
            dataset_id=dataset_id,
            evaluator=evaluator,
            batch_size=batch_size,
            resume_token=resume_token,
            metadata=metadata,
        )

    # -------------------------------------------------------------------------
    # OpenAI integration helpers (drop-in replacement)
    # -------------------------------------------------------------------------
    def get_openai_module(self):
        """
        Returns the Langfuse-wrapped OpenAI module:
            from langfuse.openai import openai
        """
        from langfuse.openai import openai  # lazy import
        return openai

    def get_openai_clients(self):
        """
        Returns OpenAI client classes wrapped by Langfuse:
            from langfuse.openai import OpenAI, AsyncOpenAI, AzureOpenAI, AsyncAzureOpenAI
        """
        from langfuse.openai import OpenAI, AsyncOpenAI, AzureOpenAI, AsyncAzureOpenAI  # lazy import
        return OpenAI, AsyncOpenAI, AzureOpenAI, AsyncAzureOpenAI

    # -------------------------------------------------------------------------
    # LangChain integration helper
    # -------------------------------------------------------------------------
    def get_langchain_callback(self):
        """
        Returns the Langfuse LangChain CallbackHandler for tracing chains/agents/tools.
        """
        from langfuse.langchain import CallbackHandler  # lazy import
        return CallbackHandler()

    # -------------------------------------------------------------------------
    # IDs, URLs, health, flush/shutdown
    # -------------------------------------------------------------------------
    def get_current_trace_id(self) -> Optional[str]:
        return self.client.get_current_trace_id()

    def get_current_observation_id(self) -> Optional[str]:
        return self.client.get_current_observation_id()

    def get_trace_url(self, trace_id: str) -> str:
        return self.client.get_trace_url(trace_id)

    def auth_check(self) -> bool:
        """
        Optional health check (avoid in hot paths). Returns True if credentials are valid.
        """
        return bool(self.client.auth_check())

    def flush(self) -> None:
        """
        Flush batched events. Call in short-lived scripts or on shutdown.
        """
        self.client.flush()

    def shutdown(self) -> None:
        """
        Graceful shutdown for long-lived apps, if needed.
        """
        self.client.shutdown()

    # -------------------------------------------------------------------------
    # Advanced: add tags to an existing trace by linking trace_context
    # (Recommended approach is to add tags in-context or use scores;
    #  editing post-creation is limited in v3 due to OTel conventions.)
    # -------------------------------------------------------------------------
    def add_tags_to_existing_trace(self, trace_id: str, tags: list[str], metadata: Optional[Dict[str, Any]] = None, name: str = "update-trace"):
        """
        Attach tags/metadata to an existing trace by creating a span in that trace context.
        Note: Editing existing traces directly by ID is discouraged in the OTel-native v3 SDK.
        """
        with self.start_span(name=name, trace_context={"trace_id": trace_id}) as span:
            span.update_trace(tags=tags, metadata=metadata)
            # span ends on context exit
