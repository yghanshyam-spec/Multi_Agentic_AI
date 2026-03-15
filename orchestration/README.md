# Generalised Orchestration Layer

## Overview

The orchestration layer is **use-case agnostic**. Any multi-agent workflow
can be expressed as a `UseCaseConfig` without modifying any agent code.

## Architecture

```
orchestration/
├── pipeline.py              ← Core engine (UseCaseConfig + run_pipeline)
├── use_cases/
│   ├── incident_response.py ← 10-agent incident response config
│   └── content_generation.py← 4-agent content pipeline config
└── README.md
```

## Defining a New Use Case

```python
from orchestration.pipeline import UseCaseConfig, StepDef, run_pipeline

my_config = UseCaseConfig(
    name="My Custom Pipeline",
    steps=[
        StepDef(id="router",    agent="router",    label="Route Request",  layer=0),
        StepDef(id="reasoning", agent="reasoning", label="Analyse",        layer=2,
                deps=["router"],
                input_fn=lambda ctx, inp: (f"Analyse: {inp}", {})),
        StepDef(id="generator", agent="generator", label="Generate Output", layer=2,
                deps=["reasoning"],
                input_fn=lambda ctx, inp: (
                    inp,
                    {"working_memory": {"strategy": ctx["reasoning"].get("conclusion")}}
                )),
    ],
)

result = run_pipeline(my_config, "Your user input here")
```

## Prompt / Config Injection

Consumer teams can override any agent's prompts without touching agent code:

```python
StepDef(
    id="reasoning",
    agent="reasoning",
    label="Custom RCA",
    layer=2,
    agent_config={
        "prompts": {
            "frame": "Your custom frame prompt: {input}",
            "cot":   "Your chain-of-thought prompt: {problem} Evidence: {evidence}",
        }
    },
)
```

## Langfuse Observability

Set environment variables to enable full tracing:

```bash
export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_SECRET_KEY=sk-lf-...
export LANGFUSE_HOST=https://cloud.langfuse.com   # optional
```

Every pipeline run creates a root Langfuse trace with child spans per step.
Prompts are fetched from the Langfuse prompt registry if keys match — with
built-in defaults as fallback.

## Available Agents

| Key            | Agent            | Layer |
|----------------|------------------|-------|
| `router`       | Router Agent     | 0     |
| `intent`       | Intent Agent     | 1     |
| `planner`      | Planner Agent    | 1     |
| `workflow`     | Workflow Agent   | 1     |
| `reasoning`    | Reasoning Agent  | 2     |
| `generator`    | Generator Agent  | 2     |
| `communication`| Communication    | 2     |
| `execution`    | Execution Agent  | 3     |
| `hitl`         | HITL Agent       | 3     |
| `audit`        | Audit Agent      | 3     |
