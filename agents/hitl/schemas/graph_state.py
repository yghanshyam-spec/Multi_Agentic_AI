from typing import TypedDict, Optional, Dict, List, Any

class HITLState(TypedDict):
    """
    Represents the state of the HITL agent workflow.
    """
    user_input: str
    agent_output: Optional[str]
    requires_human: bool
    approved: Optional[bool]
    human_feedback: Optional[str]
    checkpoint_name: Optional[str]
    metadata: Dict[str, Any]
    history: List[Dict[str, Any]]
    risk_score: float
    requires_review: bool
    extra: Dict[str, Any]

