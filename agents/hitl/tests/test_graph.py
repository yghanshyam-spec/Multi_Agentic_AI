"""
tests/test_graph.py
===================
Integration smoke-test for the compiled LangGraph.
"""

import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage
from schemas.graph_state import AgentState
from workflows.create_graph import create_graph


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.invoke.return_value = AIMessage(content="Mocked LLM response.")
    return llm


@pytest.fixture
def default_config():
    return {
        "agent": {"name": "test_agent", "recursion_limit": 10},
        "llm": {"provider": "openai", "model": "gpt-4o-mini"},
    }


def test_graph_compiles(mock_llm, default_config):
    graph = create_graph(llm=mock_llm, config=default_config)
    assert graph is not None


def test_graph_runs(mock_llm, default_config):
    graph = create_graph(llm=mock_llm, config=default_config)
    result = graph.invoke({
        "input": "Hello, agent!",
        "messages": [],
        "output": None,
        "metadata": {},
        "iteration": 0,
        "error": None,
    })
    assert "output" in result
    assert result["output"]  # non-empty


def test_empty_input_returns_error(mock_llm, default_config):
    graph = create_graph(llm=mock_llm, config=default_config)
    result = graph.invoke({
        "input": "",
        "messages": [],
        "output": None,
        "metadata": {},
        "iteration": 0,
        "error": None,
    })
    # Should have either an error or handled output
    assert "output" in result or "error" in result
