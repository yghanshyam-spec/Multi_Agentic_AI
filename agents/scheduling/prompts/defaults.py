"""agents/scheduling/prompts/defaults.py"""
PARSE_SCHEDULE_INTENT=("Parse this scheduling request.\nRequest: {user_request}\nExtract: action (create/read/update/delete), event_type (meeting/task/reminder), participants, preferred_time, duration_minutes, platform (Outlook/Teams/Google), recurrence.\nReturn structured JSON.")
CHECK_AVAILABILITY=("Given these calendar events, determine availability for a new event.\nExisting events: {existing_events}\nRequested time: {requested_time} | Duration: {duration_minutes} minutes\nReturn JSON: {{available: bool, conflicts: [str], suggested_alternatives: [str]}}")
CREATE_EVENT_PROMPT=("Compose a calendar event invitation.\nEvent: {event_details} | Participants: {participants} | Platform: {platform}\nReturn JSON: {{subject: str, body: str, accept_decline_required: bool}}")
CONFIRM_SCHEDULING=("Summarise this scheduling action for the user.\nAction: {action} | Event: {event_details} | Result: {result}\nConfirm what was scheduled, when, who is invited, and any conflicts resolved.")
_REG={"sched_parse_intent":PARSE_SCHEDULE_INTENT,"sched_check_availability":CHECK_AVAILABILITY,
      "sched_create_event":CREATE_EVENT_PROMPT,"sched_confirm":CONFIRM_SCHEDULING}
def get_default_prompt(k): return _REG.get(k,"")
