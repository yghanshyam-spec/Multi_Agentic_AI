from typing import Any, Dict, Callable
from langgraph.graph import StateGraph, END
from agent_hitl.schemas.graph_state import HITLState
from agent_hitl.workflows.checkpoint_node import checkpoint_node
# from agents.checkpoint_agent import CheckPointAgent

class GraphBuilder:
    def __init__(self, agent_node: Callable[[HITLState], HITLState], human_node: Callable[[HITLState], HITLState], config: Dict[str, Any]):
        self.agent_node = agent_node
        self.human_node = human_node
        self.config = config

    def build(self) -> StateGraph:
        """
        Constructs the StateGraph.
        """
        graph = StateGraph(HITLState)

        graph.add_node("agent", self.agent_node)
        graph.add_node("checkpoint", lambda state: checkpoint_node(state, self.config)) # Pass config to checkpoint_node
        graph.add_node("human", self.human_node)
        
        # Helper to merge human feedback
        def merge_node(state: HITLState) -> HITLState:
            if state.get("approved"):
                # Logic to apply feedback could go here
                pass
            return state

        graph.add_node("merge", merge_node)

        graph.set_entry_point("agent")

        graph.add_edge("agent", "checkpoint")

        def check_human(state: HITLState):
            if state.get("requires_human"):
                return "human"
            return "merge"

        graph.add_conditional_edges(
            "checkpoint",
            check_human,
            {"human": "human", "merge": "merge"}
        )

        graph.add_edge("human", "merge")
        graph.add_edge("merge", END)

        return graph.compile()
