from typing import Dict, Any, List
from agent_hitl.schemas.graph_state import HITLState

class CheckpointEvaluator:
    def __init__(self, config: Dict[str, Any]):
        self.checkpoints = config.get("checkpoints", [])

    def evaluate(self, state: HITLState) -> HITLState:
        """
        Evaluates the current state against configured checkpoints.
        """
        for checkpoint in self.checkpoints:
            condition = checkpoint.get("condition")
            name = checkpoint.get("name")
            
            # Simple eval for now, can be expanded to more safe evaluation
            # WARNING: eval() is unsafe, in production use a safer expression parser
            try:
                if condition and eval(condition, {"state": state}):
                    state["requires_human"] = True
                    state["checkpoint_name"] = name
                    return state
            except Exception as e:
                print(f"Error evaluating checkpoint {name}: {e}")

        state["requires_human"] = False
        state["checkpoint_name"] = None
        return state

def checkpoint_node(state: HITLState, config: Dict[str, Any]) -> HITLState:
    evaluator = CheckpointEvaluator(config.get("configurable", {}))
    return evaluator.evaluate(state)
