from typing import Dict, Any, Optional
from agent_hitl.persistence.storage import Storage

class ResumeHandler:
    def __init__(self, storage: Storage):
        self.storage = storage

    def load_state(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Loads the state for a given run_id.
        """
        return self.storage.load(run_id)

    def save_state(self, run_id: str, state: Dict[str, Any]):
        """
        Saves the state for a given run_id.
        """
        self.storage.save(run_id, state)
