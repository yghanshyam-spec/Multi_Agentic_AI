"""
agents/notification/agents/specialist_agent.py
Specialist agent for notification — extends BaseNotificationAgent with domain logic.
"""
from __future__ import annotations
from agents.notification.agents.base_agent import BaseNotificationAgent


class NotificationSpecialistAgent(BaseNotificationAgent):
    """Domain specialist for the notification agent."""

    def __init__(self, agent_config: dict | None = None, **kwargs):
        super().__init__(agent_config=agent_config, **kwargs)
