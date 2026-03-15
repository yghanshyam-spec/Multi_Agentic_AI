"""
communication/tests/test_comm_tools.py
Unit tests for communication tools (no LLM calls).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from tools.communication_tools import (
    ContextMemoryTool, ChannelDispatcher, CRMLogTool, AuditLogTool,
    EmailAdapter, SlackAdapter, TeamsAdapter, ChatAdapter,
)


@pytest.fixture
def memory():
    return ContextMemoryTool()


@pytest.fixture
def dispatcher():
    return ChannelDispatcher({"mock_mode": "true"})


# ---- ContextMemoryTool -------------------------------------------------------

def test_memory_save_and_load(memory):
    thread_id = "test-thread-001"
    entry = {"role": "user", "channel": "email", "content": "Hello world"}
    memory.save(thread_id, entry)
    history = memory.load(thread_id)
    assert len(history) >= 1
    assert history[-1]["content"] == "Hello world"


def test_memory_load_empty(memory):
    history = memory.load("nonexistent-thread-xyz")
    assert history == []


def test_memory_get_summary_empty(memory):
    summary = memory.get_summary("no-thread")
    assert "No prior" in summary


def test_memory_get_summary_populated(memory):
    tid = "summary-thread-001"
    memory.save(tid, {"role": "user", "channel": "chat", "content": "Hi there"})
    memory.save(tid, {"role": "assistant", "channel": "chat", "content": "Hello! How can I help?"})
    summary = memory.get_summary(tid)
    assert len(summary) > 5


def test_memory_max_entries(memory):
    tid = "maxtest-thread-001"
    for i in range(30):
        memory.save(tid, {"role": "user", "channel": "chat", "content": f"Message {i}"})
    history = memory.load(tid, max_entries=10)
    assert len(history) == 10


# ---- ChannelDispatcher -------------------------------------------------------

def test_dispatch_email(dispatcher):
    result = dispatcher.dispatch(
        "email", "Test response content",
        {"sender": "test@example.com", "sender_email": "test@example.com", "subject": "Test"},
        thread_id="th-001"
    )
    assert result["status"] == "simulated"
    assert result["channel"] == "email"
    assert "delivery_id" in result


def test_dispatch_slack(dispatcher):
    result = dispatcher.dispatch(
        "slack", "Slack message content",
        {"slack_channel": "#general"},
        thread_id="th-002"
    )
    assert result["status"] == "simulated"
    assert result["channel"] == "slack"


def test_dispatch_chat(dispatcher):
    result = dispatcher.dispatch(
        "chat", "Chat response",
        {"session_id": "sess-001"},
        thread_id="th-003"
    )
    assert result["status"] == "simulated"


def test_dispatch_teams(dispatcher):
    result = dispatcher.dispatch(
        "teams", "Teams message",
        {"subject": "Update"},
        thread_id="th-004"
    )
    assert result["status"] == "simulated"
    assert result["channel"] == "teams"


def test_dispatch_memo(dispatcher):
    result = dispatcher.dispatch(
        "memo", "Internal memo content",
        {"subject": "Policy Update"},
        thread_id="th-005"
    )
    assert result["status"] == "simulated"
    assert result["channel"] == "memo"


def test_dispatch_unknown_channel_fallback(dispatcher):
    result = dispatcher.dispatch(
        "sms", "SMS content",
        {"sender": "user"},
    )
    # Falls back to API adapter
    assert result.get("status") is not None


def test_dispatch_log_accumulates():
    d = ChannelDispatcher({"mock_mode": "true"})
    d.dispatch("email", "msg1", {"sender_email": "a@b.com", "subject": "s1"})
    d.dispatch("slack", "msg2", {"slack_channel": "#g"})
    log = ChannelDispatcher.get_dispatch_log()
    assert len(log) >= 2


# ---- CRMLogTool --------------------------------------------------------------

def test_crm_log_creates_entry():
    crm = CRMLogTool()
    result = crm.log(
        thread_id="t-001", session_id="s-001", workflow="omnichannel_response",
        channel="email", classification="automated_response",
        resolution="We have resolved your issue.", history=[],
    )
    assert result["success"] is True
    assert "crm_id" in result


def test_crm_log_accumulates():
    crm = CRMLogTool()
    before = len(CRMLogTool.get_log())
    crm.log("t-a", "s-a", "omnichannel_response", "chat", "automated_response", "Done", [])
    crm.log("t-b", "s-b", "broadcast_drafting", "email", "automated_response", "Sent", [])
    assert len(CRMLogTool.get_log()) >= before + 2


# ---- AuditLogTool ------------------------------------------------------------

def test_audit_log_creates_entry():
    audit = AuditLogTool()
    result = audit.log(
        event_type="OMNICHANNEL_RESPONSE",
        workflow="omnichannel_response",
        session_id="sess-audit-001",
        channels=["email", "chat"],
        details={"thread_id": "t-001"},
    )
    assert result["success"] is True
    assert len(result["audit_id"]) > 8


def test_audit_log_broadcast():
    audit = AuditLogTool()
    result = audit.log(
        event_type="BROADCAST_DRAFT",
        workflow="broadcast_drafting",
        session_id="bcast-001",
        channels=["email", "slack", "memo"],
        details={"draft_count": 3, "is_consistent": True},
    )
    assert result["success"] is True
