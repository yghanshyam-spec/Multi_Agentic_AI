"""agents/api_query/utils/logger.py — agent-scoped logger shortcut."""
from shared.common import get_logger

# Pre-configured logger for this agent — import this instead of calling get_logger()
logger = get_logger("agents.api_query")
