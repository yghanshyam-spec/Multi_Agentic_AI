"""
Example 2: Deployment Approval Workflow
========================================
Simulates a CI/CD deployment pipeline that requires
human approval before deploying to production.

Run:  python -m hitl_langgraph.examples.deployment_approval.run
"""
import sys
import os

import yaml

from agent_hitl.ui_adapters.cli_adapter import CLIAdapter
from agent_hitl.ui_adapters.streamlit_adapter import StreamlitAdapter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from agent_hitl.schemas.graph_state import HITLState
from agent_hitl.workflows.graph_builder import GraphBuilder
from agents.hitl.agents.base_agent import BaseAgent
from agent_hitl.ui_adapters.api_adapter import APIAdapter
from agent_hitl.persistence.sqlite_store import SQLiteStore
from agent_hitl.core.resume_handler import ResumeHandler
from agent_hitl.utils.helpers import create_initial_state, generate_run_id
from agent_hitl.utils.logger import get_logger

logger = get_logger("deploy_approval")


# ── Custom Agent ──────────────────────────────────────────
class DeploymentAgent(BaseAgent):
    """Validates deployment readiness and assigns risk."""

    def run(self, state):
        user_input = state["user_input"].lower()

        # Determine environment
        if "production" in user_input or "prod" in user_input:
            env = "production"
            risk = 0.9
        elif "staging" in user_input:
            env = "staging"
            risk = 0.5
        else:
            env = "development"
            risk = 0.1

        state["risk_score"] = risk
        state["metadata"]["environment"] = env
        state["agent_output"] = (
            f"Deployment Readiness Report\n"
            f"  Environment : {env}\n"
            f"  Risk Score  : {risk:.2f}\n"
            f"  Tests       : PASS - All passing\n"
            f"  Docker Image: myapp:v2.3.1\n"
            f"  Approval    : {'REQUIRED' if risk > 0.7 else 'Auto-approved'}"
        )
        return state

 

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config_deployment.yaml")

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
#                 "name": "production_deploy_gate",
#                 "condition": "state.get('risk_score', 0) > 0.7",
#                 "require_approval": True
#             }
#         ]
#     }
# }


# ── Main ──────────────────────────────────────────────────
def main():
    agent = DeploymentAgent()
    adapter =  CLIAdapter() #APIAdapter() #StreamlitAdapter()
    store = SQLiteStore(db_path="deploy_example.db")
    resume_handler = ResumeHandler(store)

    builder = GraphBuilder(
        agent_node=agent.run,
        human_node=adapter.human_node,
        config=CONFIG
    )
    app = builder.build()

    # --- Scenario 1: Deploy to staging (auto-approved) ----
    print("\n" + "=" * 60)
    print("SCENARIO 1: STAGING DEPLOYMENT (auto)")
    print("=" * 60)

    run_id = generate_run_id()
    state1 = create_initial_state("Deploy myapp to staging")
    result1 = app.invoke(state1)

    resume_handler.save_state(run_id, result1)
    print(f"  Run ID       : {run_id}")
    print(f"  requires_human: {result1['requires_human']}")
    print(f"  Output:\n{result1['agent_output']}")

    # --- Scenario 2: Deploy to production (needs approval) -
    print("\n" + "=" * 60)
    print("SCENARIO 2: PRODUCTION DEPLOYMENT (approval needed)")
    print("=" * 60)

    run_id2 = generate_run_id()
    state2 = create_initial_state("Deploy myapp to production")
    result2 = app.invoke(state2)

    resume_handler.save_state(run_id2, result2)
    print(f"  Run ID       : {run_id2}")
    print(f"  requires_human: {result2['requires_human']}")
    print(f"  Output:\n{result2['agent_output']}")
    print(f"  Approved     : {result2.get('approved')}")
    print(f"  Feedback     : {result2.get('human_feedback')}")

    # --- Show state persistence ---
    print("\n" + "=" * 60)
    print("PERSISTENCE CHECK: Resuming state from store")
    print("=" * 60)
    loaded = resume_handler.load_state(run_id2)
    print(f"  Loaded Run   : {run_id2}")
    print(f"  Environment  : {loaded['metadata'].get('environment')}")
    print(f"  Approved     : {loaded.get('approved')}")

    # Cleanup
    store.close()
    if os.path.exists("deploy_example.db"):
        os.unlink("deploy_example.db")


if __name__ == "__main__":
    main()
