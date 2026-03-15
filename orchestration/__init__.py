"""
orchestration — generalised agent orchestration layer.

Exports
-------
run_pipeline         : execute a declarative UseCaseConfig
run_auto             : fully automatic execution from natural language
build_auto_pipeline  : build a UseCaseConfig from natural language (no run)
inspect_plan         : preview the auto-generated execution plan (no run)
UseCaseConfig        : declarative pipeline config dataclass
StepDef              : single step config dataclass
PipelineResult       : full pipeline result dataclass
"""
from .pipeline import (
    run_pipeline, UseCaseConfig, StepDef, PipelineResult,
    StepResult, AgentStepRunner,
)
from .auto_orchestrator import (
    run_auto, build_auto_pipeline, inspect_plan,
    analyse_request, AgentPlan, AutoPipelineResult,
    AGENT_CAPABILITIES,
)

__all__ = [
    "run_pipeline", "UseCaseConfig", "StepDef", "PipelineResult",
    "StepResult", "AgentStepRunner",
    "run_auto", "build_auto_pipeline", "inspect_plan",
    "analyse_request", "AgentPlan", "AutoPipelineResult",
    "AGENT_CAPABILITIES",
]
