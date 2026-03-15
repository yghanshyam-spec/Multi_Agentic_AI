# Agentic AI Accelerator v4

## What Changed in v4

### 1. Scheduler → Router
The `agents/scheduler/` folder has been renamed to `agents/router/`.
The agent's core job is **routing** — analysing requests, checking agent load, planning optimal routing,
activating agents, and synthesising results. "Router" communicates this purpose more accurately than
"Scheduler" (which implies time-based scheduling). A `run_scheduler` backward-compat alias is preserved.

### 2. Full Sub-Folder Structure for All Agents
Every agent now follows the same consistent structure:

```
agents/<agent_name>/
├── graph.py           ← LangGraph entry-point + public run_* function
├── nodes/
│   └── <agent>_nodes.py   ← All node functions (logic lives here)
├── tools/
│   └── <tool>.py          ← Agent-specific tools (e.g. load_monitor, sandbox)
├── prompts/
│   └── defaults.py        ← Built-in prompt defaults
├── schemas/
│   └── state.py           ← State extensions / aliases
├── config/                ← Consumer YAML configs (drop-in overrides)
└── tests/                 ← Agent unit tests
```

### 3. Consumer-Side Prompt + Config Injection
Prompts and config are **never hardcoded** into agent logic. They flow from the consumer:

```
Consumer Use Case Config
       │
       ▼  agent_config["prompts"]["<key>"]
  run_<agent>(agent_config=...)
       │
       ▼  _p(key, state)  in each node
  shared.langfuse_manager.get_prompt()
       │
       ├── 1. Langfuse prompt registry  (if configured)
       ├── 2. Consumer agent_config["prompts"]
       └── 3. agents/<agent>/prompts/defaults.py  (built-in fallback)
```

### 4. Langfuse LLM Engineering (shared/langfuse_manager.py)
Centralised Langfuse integration used by **all** agents:
- **Traces**: every `run_*` function wraps its execution in a Langfuse trace
- **Spans**: every node call is optionally tracked as a child span
- **Generations**: every `call_llm()` is logged as a Langfuse generation
- **Prompt registry**: prompts are fetched from Langfuse first, falling back to built-ins

Enable with env vars:
```bash
export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_SECRET_KEY=sk-lf-...
```

### 5. Generalised Orchestration Layer
`orchestration/pipeline.py` is now **completely use-case agnostic**.
Any workflow is defined as a `UseCaseConfig` — no pipeline code changes needed.

Two built-in use cases:
- `orchestration/use_cases/incident_response.py` — full 10-agent production incident pipeline
- `orchestration/use_cases/content_generation.py` — 4-agent content generation pipeline

## Project Structure

```
agentic_accelerator/
├── README.md
├── main.py                           ← CLI entry point
├── requirements.txt
│
├── shared/                           ← Universal shared layer
│   ├── state.py                      ← All TypedDict state schemas + enums
│   ├── llm_factory.py                ← LLM abstraction (Claude / MockLLM)
│   ├── langfuse_manager.py           ← NEW: Langfuse tracing + prompt registry
│   └── utils.py                      ← build_trace_entry, safe_get, etc.
│
├── agents/
│   ├── router/                       ← Layer 0: Router (formerly Scheduler)
│   ├── intent/                       ← Layer 1: Intent Classification
│   ├── planner/                      ← Layer 1: Task Planning
│   ├── workflow/                     ← Layer 1: Workflow Orchestration
│   ├── reasoning/                    ← Layer 2: Chain-of-Thought Reasoning
│   ├── generator/                    ← Layer 2: Document Generation
│   ├── communication/                ← Layer 2: Multi-channel Communication
│   ├── execution/                    ← Layer 3: Sandboxed Execution + HITL + Audit runners
│   ├── hitl/                         ← Layer 3: Human-in-the-Loop (LangGraph sub-package)
│   └── audit/                        ← Layer 3: Compliance Audit proxy
│
├── orchestration/
│   ├── pipeline.py                   ← Generalised pipeline engine
│   ├── use_cases/
│   │   ├── incident_response.py      ← 10-step incident response config
│   │   └── content_generation.py    ← 4-step content generation config
│   └── README.md
│
└── test_agents/                      ← Use case test fixtures
    ├── comm_use_case_1/
    ├── comm_use_case_2/
    ├── hitl_use_case_1/
    └── hitl_use_case_2/
```

## Quick Start

```bash
# Run default use case (production incident response)
python main.py

# Run content generation pipeline
python main.py --use-case content

# Custom input
python main.py --input "Diagnose why our checkout service is slow"

# Output full JSON
python main.py --json
```

## Environment Variables

| Variable              | Purpose                          | Default            |
|-----------------------|----------------------------------|--------------------|
| `ANTHROPIC_API_KEY`   | Real Claude LLM (vs MockLLM)     | unset → MockLLM    |
| `LANGFUSE_PUBLIC_KEY` | Langfuse observability           | unset → disabled   |
| `LANGFUSE_SECRET_KEY` | Langfuse observability           | unset → disabled   |
| `LANGFUSE_HOST`       | Self-hosted Langfuse URL         | cloud.langfuse.com |
| `LANGFUSE_ENABLED`    | Force enable/disable ("true"/"false") | auto-detect   |

## Layers

| Layer | Agents                                     | Responsibility                    |
|-------|--------------------------------------------|-----------------------------------|
| 0     | Router                                     | Routing, orchestration, synthesis |
| 1     | Intent, Planner, Workflow                  | Decomposition & planning          |
| 2     | Reasoning, Generator, Communication        | Core intelligence & output        |
| 3     | Execution, HITL, Audit                     | Governance & execution            |
