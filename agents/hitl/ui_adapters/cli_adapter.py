from typing import Dict, Any
from agent_hitl.schemas.graph_state import HITLState
from agent_hitl.utils.logger import get_logger

logger = get_logger("hitl.cli")


class CLIAdapter:
    """
    Command-line interface adapter for human-in-the-loop interaction.
    Prompts the user in the terminal for approval/rejection.
    """

    def human_node(self, state: HITLState) -> HITLState:
        """
        Presents the agent output to the human and asks for approval.
        """
        print("\n" + "=" * 60)
        print("🔔 HUMAN REVIEW REQUIRED")
        print("=" * 60)
        print(f"📋 Checkpoint: {state.get('checkpoint_name', 'Unknown')}")
        print(f"📝 Agent Output:\n{state.get('agent_output', 'No output')}")
        print("=" * 60)

        while True:
            response = input("\n✅ Approve? (yes/no): ").strip().lower()
            if response in ("yes", "y"):
                state["approved"] = True
                feedback = input("💬 Any feedback (press Enter to skip): ").strip()
                state["human_feedback"] = feedback if feedback else None
                logger.info("Human APPROVED the action.")
                break
            elif response in ("no", "n"):
                state["approved"] = False
                feedback = input("💬 Reason for rejection: ").strip()
                state["human_feedback"] = feedback if feedback else "Rejected without reason."
                logger.info("Human REJECTED the action.")
                break
            else:
                print("❌ Invalid input. Please enter 'yes' or 'no'.")

        return state
