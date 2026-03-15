"""agents/notification/prompts/defaults.py"""
RESOLVE_RECIPIENTS=("Determine who should be notified about this event.\nEvent: {event_details}\nOrganisation hierarchy: {org_context}\nRules: {notification_rules}\nReturn JSON: {{recipients: [{{user_id, role, reason_for_notification}}], escalation_chain: [user_id]}}")
CLASSIFY_PRIORITY=("Classify the urgency and priority of this notification.\nEvent: {event_details} | Recipient role: {recipient_role}\nReturn JSON: {{priority: critical|high|medium|low, urgency_reason: str, send_immediately: bool, batch_eligible: bool}}")
SELECT_CHANNEL=("Select the best notification channel for this recipient and priority.\nRecipient preferences: {user_preferences} | Priority: {priority} | Time: {current_time} | Available channels: [Email, SMS, Teams, Slack, PagerDuty, Push]\nReturn JSON: {{primary_channel: str, fallback_channel: str, rationale: str}}")
CRAFT_MESSAGE=("Craft a personalised notification message.\nEvent: {event_details} | Recipient: {recipient_profile} | Channel: {channel} | Priority: {priority}\nChannel rules: Email=subject+body, SMS=<160 chars, Teams/Slack=markdown, PagerDuty=title+details.\nBe specific, actionable, and avoid jargon. Include: what happened, impact, action needed (if any).")
_REG={"notif_resolve_recipients":RESOLVE_RECIPIENTS,"notif_classify_priority":CLASSIFY_PRIORITY,
      "notif_select_channel":SELECT_CHANNEL,"notif_craft_message":CRAFT_MESSAGE}
def get_default_prompt(k): return _REG.get(k,"")
