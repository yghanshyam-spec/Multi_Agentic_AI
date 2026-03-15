# Communication Agent Accelerator

Standardizes multi-channel communication handling (chat, email, API, Slack, Teams)
with context retention and response orchestration. Built on **LangGraph** with
**Langfuse** prompt management and full mock support for local development.

---

## Architecture

```
agent_communication/
├── config/
│   ├── agent_config.yaml            Root accelerator config
│   ├── llm_config.yaml              LLM provider settings
│   ├── prompts_config.yaml          Prompt registry (Langfuse + YAML fallbacks)
│   └── workflows/
│       ├── omnichannel_response.yaml   UC1 graph config
│       └── broadcast_drafting.yaml     UC2 graph config
├── core/
│   ├── engine.py                    CommunicationAgentEngine (main entry point)
│   └── provider.py                  OpenAI / Anthropic / Azure LLM factory
├── agents/
│   ├── base_agent.py                Abstract base with LLM invocation + JSON parsing
│   └── specialist_agent.py          CommunicationSpecialistAgent
├── tools/
│   └── communication_tools.py       All channel adapters + memory + CRM + audit
├── workflows/
│   ├── create_graph.py              Dynamic LangGraph assembly from YAML
│   ├── edges.py                     Conditional routing (bool-key safe)
│   └── nodes/
│       ├── omnichannel_nodes.py     7 node functions for UC1
│       └── broadcast_nodes.py       7 node functions for UC2
├── schemas/
│   ├── graph_state.py               TypedDict states (Omnichannel + Broadcast)
│   └── output_models.py             Pydantic response models
├── prompts/
│   └── prompt_manager.py            3-tier: Langfuse > YAML > built-in defaults
├── observability/
│   └── langfuse_client.py           Tracing wrapper (graceful no-op fallback)
├── guardrails/
│   └── policy_engine.py             Input safety + PII detection
├── utils/
│   ├── logger.py                    Structured text/JSON logging
│   ├── helpers.py                   Channel, string, sentiment utilities
│   ├── decorators.py                Retry + timing decorators
│   └── config_loader.py             YAML loader with \${ENV:default} interpolation
├── tests/                           Unit + integration tests
└── test_agents/
    ├── use_case_1/                  Omnichannel runner + scenarios
    └── use_case_2/                  Broadcast drafting runner + scenarios
```

---

## Use Cases

### Use Case 1 -- Omnichannel Customer Response

> *Customer complaint arrives via email, follow-up via chat, escalation via voice.*

**7-node workflow:**
```
detect_channel_node     -- Channel detection & payload normalisation
  -> load_context_node       -- Load unified conversation history
  -> classify_message_node   -- automated_response | human_escalation | acknowledgement
  -> draft_response_node     -- Channel-aware LLM drafting (tone + length adapted)
  -> check_consistency_node  -- Check draft vs. prior thread history
  -> dispatch_response_node  -- Route to correct adapter (SMTP/Slack/Teams/Chat/API)
  -> update_context_node     -- Persist history + CRM log + audit entry
```

### Use Case 2 -- Internal Broadcast Drafting

> *Communications manager enters talking points -> agent drafts email, Slack, formal memo.*

**7-node workflow (same node names, different factory):**
```
detect_channel_node     -- Extract talking points + target channels
  -> load_context_node       -- Load prior broadcast context
  -> classify_message_node   -- Always: automated_response
  -> draft_response_node     -- Draft EACH channel version simultaneously
  -> check_consistency_node  -- Cross-channel factual consistency check
  -> dispatch_response_node  -- Dispatch all versions to their adapters
  -> update_context_node     -- Persist drafts, delivery status, audit log
```

---

## Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run Use Case 1 (Omnichannel)
```bash
cd agent_communication

python test_agents/use_case_1/run_uc1.py                    # interactive
python test_agents/use_case_1/run_uc1.py --demo             # 3-message demo
python test_agents/use_case_1/run_uc1.py --scenarios        # run all scenarios
python test_agents/use_case_1/run_uc1.py --scenario-id UC1-001
```

### Run Use Case 2 (Broadcast)
```bash
cd agent_communication

python test_agents/use_case_2/run_uc2.py                    # interactive
python test_agents/use_case_2/run_uc2.py --demo             # WFH policy demo
python test_agents/use_case_2/run_uc2.py --scenarios        # run all scenarios
python test_agents/use_case_2/run_uc2.py --scenario-id UC2-001
```

### Run Tests
```bash
pytest tests/ -v
```

---

## Configuration

### Single Config File per Use Case

Each test application uses one consolidated `agent_config.yaml`:

```yaml
# All settings in one file per use case

channels:
  mock_mode: "true"       # No real API calls -- use mock adapters
  slack_webhook_url: ""   # Set for production

llm:
  provider: "openai"
  providers:
    openai:
      model: "gpt-4o"
      temperature: 0.3

prompts:
  comm_draft_response:
    langfuse_name: "comm_draft_response_support"
    version: "latest"
    fallback: |             # Used when Langfuse is unavailable
      Draft a {tone} response for channel {channel}...

workflows:
  omnichannel_response:
    graph_config: "config/workflows/omnichannel_response.yaml"
```

### Programmatic Config Injection

```python
from core.engine import CommunicationAgentEngine

engine = CommunicationAgentEngine(
    config_dict={
        "channels": {"mock_mode": "true"},
        "llm": {"provider": "openai", "providers": {"openai": {"model": "gpt-4o"}}},
        "workflows": {
            "omnichannel_response": {
                "graph_config": "config/workflows/omnichannel_response.yaml"
            }
        },
        "observability": {"langfuse_enabled": False},
    },
    env_file=".env",
)

# Use Case 1: process an inbound email
result = engine.run(
    workflow="omnichannel_response",
    session_id="customer-thread-001",
    inbound_payload={
        "channel": "email",
        "sender": "customer@example.com",
        "subject": "Missing order",
        "body": "My order hasn't arrived after 2 weeks...",
    },
)
print(result.message)  # Drafted response
print(result.reply_channel)  # email

# Use Case 2: draft a broadcast
result = engine.run(
    workflow="broadcast_drafting",
    session_id="broadcast-001",
    talking_points="- Policy effective March 1\n- WFH 3 days/week allowed",
    target_channels=["email", "slack", "memo"],
)
for draft in result.channel_drafts:
    print(f"{draft['channel'].upper()}:", draft["content"][:100])
```

---

## Channels

| Channel | Adapter | Mock | Production |
|---------|---------|------|------------|
| email   | EmailAdapter | In-memory log | SMTP / SendGrid |
| chat    | ChatAdapter  | In-memory log | WebSocket / REST API |
| slack   | SlackAdapter | In-memory log | Slack Incoming Webhooks |
| teams   | TeamsAdapter | In-memory log | Teams Adaptive Cards webhook |
| api     | APICallbackAdapter | In-memory log | REST callback URL |
| memo    | MemoAdapter  | In-memory log | File store / SharePoint |

Set `COMM_MOCK_MODE=false` and provide real credentials in `.env` for production.

---

## LLM Providers

| Provider | Env Var | Default Model |
|----------|---------|---------------|
| OpenAI | `OPENAI_API_KEY` | `gpt-4o` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-sonnet-4-20250514` |
| Azure OpenAI | `AZURE_OPENAI_API_KEY` | `AZURE_OPENAI_DEPLOYMENT` |

Set `LLM_PROVIDER=anthropic` to switch.

---

## Prompt Management

Three-tier resolution priority:

1. **Langfuse registry** -- live versioned prompts from cloud.langfuse.com
2. **Local YAML fallback** -- `prompts:` section in `agent_config.yaml`
3. **Built-in defaults** -- `prompts/prompt_manager.py`

Enable Langfuse: set `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` in `.env`,
and `langfuse_enabled: true` in `agent_config.yaml`.

---

## Channel Rules (configurable per use case)

```yaml
channel_rules:
  email:
    tone: "professional"
    max_words: 300
    format: "paragraphs"
  slack:
    tone: "conversational_direct"
    max_words: 150
    format: "bullet_points"
  memo:
    tone: "formal_authoritative"
    max_words: 600
    format: "formal_memo"
```

These are injected into the LLM prompt dynamically -- no tone or length logic
is hardcoded in the accelerator.
