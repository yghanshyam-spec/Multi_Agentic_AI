from __future__ import annotations
import uuid
from typing import Dict, Any
from agent_hitl.schemas.graph_state import HITLState



import re
from datetime import datetime, timezone

def generate_run_id() -> str:
    """Generate a unique run ID."""
    return str(uuid.uuid4())


def create_initial_state(user_input: str, **kwargs) -> HITLState:
    """
    Create an initial HITLState from user input.
    """
    return HITLState(
        user_input=user_input,
        agent_output=None,
        requires_human=False,
        approved=None,
        human_feedback=None,
        checkpoint_name=None,
        metadata=kwargs.get("metadata", {}),
        history=[],
        risk_score=0.0,
        requires_review=False,
        extra={}
    )



 


def slugify(text: str) -> str:
    """Convert a string to a lowercase slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def truncate(text: str, max_chars: int = 200, suffix: str = "…") -> str:
    return text if len(text) <= max_chars else text[:max_chars] + suffix
