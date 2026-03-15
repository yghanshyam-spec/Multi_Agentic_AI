"""
Example 1: Customer Support Escalation Bot
============================================
Demonstrates a support agent that escalates to a human
when the customer's sentiment is negative (high risk).

Run:  python -m hitl_langgraph.examples.support_bot.run
"""
import sys
import os

import yaml


import sys
from pathlib import Path

# Append repo root to sys.path dynamically
ROOT = Path(__file__).resolve().parents[2]  # support_bot.py -> use_case_1 -> test_agent -> <repo_root>
sys.path.append(str(ROOT))

from agent_hitl.ui_adapters.streamlit_adapter import StreamlitAdapter
 

# sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from agent_hitl.schemas.graph_state import HITLState
from agent_hitl.workflows.graph_builder import GraphBuilder
from agents.hitl.agents.base_agent import BaseAgent
from agent_hitl.ui_adapters.api_adapter import APIAdapter
from agent_hitl.utils.helpers import create_initial_state
from agent_hitl.utils.logger import get_logger

logger = get_logger("support_bot")


# ── Custom Agent ──────────────────────────────────────────
class SupportAgent(BaseAgent):
    """Analyses customer message and assigns a risk score."""

    NEGATIVE_KEYWORDS = ["angry", "furious", "cancel", "terrible", "worst", "lawsuit", "complain"]

    def run(self, state):
        user_input = state["user_input"].lower()

        # Simple keyword-based sentiment scoring
        hits = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in user_input)
        risk_score = min(hits * 0.4, 1.0)

        state["risk_score"] = risk_score
        state["agent_output"] = (
            f"Customer message analysed.\n"
            f"  Risk Score : {risk_score:.2f}\n"
            f"  Escalation : {'YES — requires human review' if risk_score > 0.7 else 'No — auto-handled'}\n"
            f"  Draft Reply: \"Thank you for reaching out. We're looking into your concern.\""
        )
        logger.info(f"Risk score = {risk_score:.2f}")
        return state


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config_support.yaml")

def load_config():
    with open(CONFIG_PATH, 'r') as file:
        try:
            config = yaml.safe_load(file)
            return config
        except yaml.YAMLError as exc:
            print(f"Error parsing YAML: {exc}")

# Usage
CONFIG = load_config()

# # ── Config ────────────────────────────────────────────────
# CONFIG = {
#     "configurable": {
#         "checkpoints": [
#             {
#                 "name": "escalation_review",
#                 "condition": "state.get('risk_score', 0) > 0.7",
#                 "require_approval": True
#             }
#         ]
#     }
# }


# ── Main ──────────────────────────────────────────────────
def main():
    agent = SupportAgent()
    adapter = StreamlitAdapter() #APIAdapter()

    builder = GraphBuilder(
        agent_node=agent.run,
        human_node=adapter.human_node,
        config=CONFIG
    )
    app = builder.build()

    # --- Scenario 1: calm customer (no escalation) --------
    print("\n" + "=" * 60)
    print("SCENARIO 1: LOW-RISK CUSTOMER MESSAGE")
    print("=" * 60)
    state1 = create_initial_state("Hi, I'd like to know my order status please.")
    result1 = app.invoke(state1)
    print(f"  requires_human : {result1['requires_human']}")
    print(f"  agent_output   :\n{result1['agent_output']}")
    print(f"  approved       : {result1.get('approved')}")

    # --- Scenario 2: angry customer (escalation) ----------
    print("\n" + "=" * 60)
    print("SCENARIO 2: HIGH-RISK CUSTOMER MESSAGE")
    print("=" * 60)
    state2 = create_initial_state(
        "I am furious! This is the worst service ever. I want to cancel and file a complaint!"
    )
    result2 = app.invoke(state2)
    print(f"  requires_human : {result2['requires_human']}")
    print(f"  agent_output   :\n{result2['agent_output']}")
    print(f"  approved       : {result2.get('approved')}")
    print(f"  feedback       : {result2.get('human_feedback')}")


if __name__ == "__main__":
    main()
