from typing import Dict, Any
from agent_hitl.schemas.graph_state import HITLState
from agent_hitl.utils.logger import get_logger

logger = get_logger("hitl.api")


class APIAdapter:
    """
    API adapter stub for HTTP-based human-in-the-loop interaction.
    This adapter auto-approves for demo purposes.
    In production, this would expose HTTP endpoints.
    """

    def __init__(self):
        self._pending_reviews: Dict[str, HITLState] = {}

    def human_node(self, state: HITLState) -> HITLState:
        """
        Simulates an API-based human review.
        In production: saves state and waits for HTTP callback.
        For demo: auto-approves.
        """
        logger.info(f"API Review requested for checkpoint: {state.get('checkpoint_name')}")
        logger.info(f"Agent output: {state.get('agent_output')}")

        # Auto-approve for demonstration
        state["approved"] = True
        state["human_feedback"] = "Auto-approved via API adapter (demo mode)"
        logger.info("Auto-approved via API adapter.")

        return state
