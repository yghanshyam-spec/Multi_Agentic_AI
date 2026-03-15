# Agent Hitl

> An AI agent built with LangGraph.

## Project Structure

```
agent_hitl/
├── config/                 # YAML settings for LLMs & environment
├── core/                   # Main engine & LLM provider wrappers
├── data/                   # Raw data & vector memory stores
├── schemas/                # Shared graph state & output models
├── agents/                 # Base and specialist agent classes
├── tools/                  # External API / tool integrations
├── workflows/              # LangGraph graph assembly & node logic
├── utils/                  # Logging, helpers, decorators
├── prompts/                # Prompt templates (Langfuse-backed)
├── observability/          # Traces, metrics, Langfuse wrappers
├── guardrails/             # Safety & ethics policies
└── tests/                  # Unit & integration tests
```

## Quick Start

```bash
# 1. Create and activate virtual environment
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env  # then fill in your API keys

# 4. Run the agent
python -m agent_hitl.core.engine
```

## Architecture

This project uses **LangGraph** for stateful, multi-actor orchestration:

- **Graph State** (`schemas/graph_state.py`) — the single source of truth passed between nodes
- **Nodes** (`workflows/nodes/`) — pure functions that read/write state
- **Edges** (`workflows/edges.py`) — conditional routing between nodes
- **Graph** (`workflows/create_graph.py`) — assembles and compiles the StateGraph
- **Engine** (`core/engine.py`) — initialises providers and invokes the graph

## Author

Your Name
