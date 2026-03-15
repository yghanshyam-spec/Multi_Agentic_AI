"""agents/audit/utils/decorators.py — agent-specific decorator shortcuts."""
from shared.common import retry, log_call, with_timeout

# Re-export shared decorators
__all__ = ["retry", "log_call", "with_timeout"]
