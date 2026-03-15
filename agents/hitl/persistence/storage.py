from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class Storage(ABC):
    @abstractmethod
    def save(self, run_id: str, state: Dict[str, Any]):
        pass

    @abstractmethod
    def load(self, run_id: str) -> Optional[Dict[str, Any]]:
        pass
