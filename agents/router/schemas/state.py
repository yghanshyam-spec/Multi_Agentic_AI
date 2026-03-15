"""agents/router/schemas/state.py — RouterAgentState extension."""
from __future__ import annotations
from shared.state import SchedulerAgentState

# RouterAgentState is an alias — the accelerator-wide SchedulerAgentState
# already contains all required fields. We re-export under the new name so
# internal imports are consistent.
RouterAgentState = SchedulerAgentState
