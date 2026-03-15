"""
tests/test_agents.py
====================
Unit tests for individual agent classes.
"""

import pytest
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage
from agents.specialist_agent import SpecialistAgent


@pytest.fixture
def agent():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="Test answer.")
    return SpecialistAgent(llm=mock_llm, config={})


def test_specialist_agent_returns_output(agent):
    state = {
        "input": "What is 2+2?",
        "messages": [],
        "output": None,
        "metadata": {},
        "iteration": 0,
        "error": None,
    }
    result = agent.run(state)
    assert result["output"] == "Test answer."
    assert result["iteration"] == 1
