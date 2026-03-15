"""agents/scheduling/tools/calendar_connector.py — mock calendar connector."""
from shared import new_id,utc_now
class CalendarConnector:
    def __init__(self,config=None): self.config=config or {}
    def get_events(self,user_id:str,date_range:dict)->list:
        return [{"id":new_id("evt"),"subject":"Team Standup","start":"2025-03-11T09:00:00Z","end":"2025-03-11T09:30:00Z","organiser":"alice@company.com"}]
    def create_event(self,event:dict)->dict:
        return {"event_id":new_id("evt"),"status":"CREATED","meeting_url":f"https://teams.microsoft.com/meet/{new_id('m')}","created_at":utc_now()}
    def update_event(self,event_id:str,updates:dict)->dict:
        return {"event_id":event_id,"status":"UPDATED","updated_at":utc_now()}
