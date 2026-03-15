"""
communication/tests/test_graph_integration.py
Integration tests for graph, routing, prompts, and node wiring.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(
        content='{"classification": "automated_response", "priority": "medium", '
                '"sentiment": "neutral", "topic": "general", '
                '"requires_human": false, "escalation_reason": null}'
    )
    return llm


@pytest.fixture
def mock_pm():
    from prompts.prompt_manager import PromptManager
    pm = MagicMock(spec=PromptManager)
    pm.get.return_value = "mock prompt text"
    return pm


# ---- Router tests -----------------------------------------------------------

def test_router_bool_keys():
    from workflows.edges import build_conditional_router
    routes = {True: "node_a", False: "node_b"}
    r = build_conditional_router("classification.requires_human", routes)
    assert r({"classification": {"requires_human": True}}) == "node_a"
    assert r({"classification": {"requires_human": False}}) == "node_b"


def test_router_string_keys():
    from workflows.edges import build_conditional_router
    routes = {"automated_response": "draft", "human_escalation": "escalate"}
    r = build_conditional_router("classification.classification", routes, default="draft")
    state = {"classification": {"classification": "automated_response"}}
    assert r(state) == "draft"


def test_router_default_fallback():
    from workflows.edges import build_conditional_router
    routes = {True: "a"}
    r = build_conditional_router("flag", routes, default="default_node")
    assert r({"flag": False}) == "default_node"


def test_router_nested_field():
    from workflows.edges import build_conditional_router
    routes = {"high": "urgent_flow", "medium": "normal_flow"}
    r = build_conditional_router("classification.priority", routes, default="normal_flow")
    state = {"classification": {"priority": "high"}}
    assert r(state) == "urgent_flow"


def test_router_missing_returns_default():
    from workflows.edges import build_conditional_router
    routes = {"yes": "a", "no": "b"}
    r = build_conditional_router("missing.field", routes, default="b")
    assert r({}) == "b"


# ---- Config loader tests ----------------------------------------------------

def test_config_loader_env_interpolation(tmp_path):
    import os
    from utils.config_loader import ConfigLoader
    f = tmp_path / "test.yaml"
    f.write_text("key: ${TEST_COMM_VAR:fallback_val}\n")
    os.environ["TEST_COMM_VAR"] = "injected"
    result = ConfigLoader().load(str(f))
    assert result["key"] == "injected"
    del os.environ["TEST_COMM_VAR"]


def test_config_loader_default_when_absent(tmp_path):
    from utils.config_loader import ConfigLoader
    f = tmp_path / "test.yaml"
    f.write_text("key: ${ABSENT_COMM_VAR_XYZ:my_default}\n")
    result = ConfigLoader().load(str(f))
    assert result["key"] == "my_default"


# ---- Prompt manager tests ---------------------------------------------------

def test_prompt_manager_builtin_detect_channel():
    from prompts.prompt_manager import PromptManager
    pm = PromptManager({})
    result = pm.get("comm_detect_channel", payload='{"channel": "email"}')
    assert "email" in result


def test_prompt_manager_builtin_classify():
    from prompts.prompt_manager import PromptManager
    pm = PromptManager({})
    result = pm.get("comm_classify_message",
                    channel="email", body="I am very upset", context_summary="First contact")
    assert "automated_response" in result or "classification" in result


def test_prompt_manager_yaml_override():
    from prompts.prompt_manager import PromptManager
    config = {"prompts": {"custom_key": {"fallback": "Hello from {channel}!"}}}
    pm = PromptManager(config)
    assert pm.get("custom_key", channel="email") == "Hello from email!"


def test_prompt_manager_string_override():
    from prompts.prompt_manager import PromptManager
    config = {"prompts": {"comm_broadcast_draft": "Simple {channel} template"}}
    pm = PromptManager(config)
    result = pm.get("comm_broadcast_draft", channel="slack",
                    channel_rules="{}", talking_points="test", tone="casual",
                    max_length=100)
    assert "slack" in result


# ---- Helper tests -----------------------------------------------------------

def test_generate_thread_id_deterministic():
    from utils.helpers import generate_thread_id
    t1 = generate_thread_id("email", "user@test.com", "subject")
    t2 = generate_thread_id("email", "user@test.com", "subject")
    assert t1 == t2


def test_generate_thread_id_different_channels():
    from utils.helpers import generate_thread_id
    t1 = generate_thread_id("email", "user@test.com", "subject")
    t2 = generate_thread_id("slack", "user@test.com", "subject")
    assert t1 != t2


def test_sentiment_hint():
    from utils.helpers import sentiment_hint
    assert sentiment_hint("I am so angry and frustrated!") == "negative"
    assert sentiment_hint("Thank you so much, great service!") == "positive"
    assert sentiment_hint("Please let me know when ready.") == "neutral"


def test_word_count():
    from utils.helpers import word_count
    assert word_count("hello world this is five") == 5


# ---- Node wiring tests ------------------------------------------------------

def test_omnichannel_nodes_factory(mock_llm, mock_pm):
    from tools.communication_tools import (
        ContextMemoryTool, ChannelDispatcher, CRMLogTool, AuditLogTool
    )
    from agents.specialist_agent import CommunicationSpecialistAgent
    from workflows.nodes.omnichannel_nodes import make_omnichannel_nodes

    agent = CommunicationSpecialistAgent(mock_llm, mock_pm)
    tools = {
        "memory":     ContextMemoryTool(),
        "dispatcher": ChannelDispatcher({"mock_mode": "true"}),
        "crm":        CRMLogTool(),
        "audit":      AuditLogTool(),
    }
    nodes = make_omnichannel_nodes(agent, tools, {})
    expected = [
        "detect_channel_node", "load_context_node", "classify_message_node",
        "draft_response_node", "check_consistency_node",
        "dispatch_response_node", "update_context_node",
    ]
    for n in expected:
        assert n in nodes, f"Missing node: {n}"
        assert callable(nodes[n])


def test_broadcast_nodes_factory(mock_llm, mock_pm):
    from tools.communication_tools import (
        ContextMemoryTool, ChannelDispatcher, CRMLogTool, AuditLogTool
    )
    from agents.specialist_agent import CommunicationSpecialistAgent
    from workflows.nodes.broadcast_nodes import make_broadcast_nodes

    agent = CommunicationSpecialistAgent(mock_llm, mock_pm)
    tools = {
        "memory":     ContextMemoryTool(),
        "dispatcher": ChannelDispatcher({"mock_mode": "true"}),
        "crm":        CRMLogTool(),
        "audit":      AuditLogTool(),
    }
    nodes = make_broadcast_nodes(agent, tools, {})
    expected = [
        "detect_channel_node", "load_context_node", "classify_message_node",
        "draft_response_node", "check_consistency_node",
        "dispatch_response_node", "update_context_node",
    ]
    for n in expected:
        assert n in nodes, f"Missing node: {n}"
        assert callable(nodes[n])


def test_detect_channel_node_email(mock_llm, mock_pm):
    """Verify detect_channel_node correctly identifies email from payload."""
    from tools.communication_tools import (
        ContextMemoryTool, ChannelDispatcher, CRMLogTool, AuditLogTool
    )
    from agents.specialist_agent import CommunicationSpecialistAgent
    from workflows.nodes.omnichannel_nodes import make_omnichannel_nodes

    agent = CommunicationSpecialistAgent(mock_llm, mock_pm)
    tools = {
        "memory": ContextMemoryTool(),
        "dispatcher": ChannelDispatcher({"mock_mode": "true"}),
        "crm": CRMLogTool(), "audit": AuditLogTool(),
    }
    nodes = make_omnichannel_nodes(agent, tools, {})
    detect = nodes["detect_channel_node"]

    state = {
        "session_id": "test-sess-001",
        "trace_id": "trace-001",
        "workflow": "omnichannel_response",
        "user_message": "Hello",
        "metadata": {},
        "inbound_payload": {
            "sender_email": "user@example.com",
            "subject": "Test",
            "body": "Hello there",
        },
    }
    result = detect(state)
    assert result["detected_channel"] == "email"
    assert result["normalised_message"]["body"] == "Hello there"


def test_classify_escalation_keywords(mock_llm, mock_pm):
    """Verify escalation keywords trigger human escalation override."""
    from tools.communication_tools import (
        ContextMemoryTool, ChannelDispatcher, CRMLogTool, AuditLogTool
    )
    from agents.specialist_agent import CommunicationSpecialistAgent
    from workflows.nodes.omnichannel_nodes import make_omnichannel_nodes

    agent = CommunicationSpecialistAgent(mock_llm, mock_pm)
    tools = {
        "memory": ContextMemoryTool(),
        "dispatcher": ChannelDispatcher({"mock_mode": "true"}),
        "crm": CRMLogTool(), "audit": AuditLogTool(),
    }
    nodes = make_omnichannel_nodes(agent, tools, {})
    classify = nodes["classify_message_node"]

    state = {
        "normalised_message": {
            "channel": "email",
            "body": "This is unacceptable. I am consulting a lawyer.",
            "thread_id": "t-001",
        },
        "context_summary": "",
        "trace_id": "trace-001",
    }
    result = classify(state)
    cls = result["classification"]
    assert cls["requires_human"] is True
    assert cls["classification"] == "human_escalation"
