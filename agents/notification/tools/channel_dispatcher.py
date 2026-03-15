"""agents/notification/tools/channel_dispatcher.py — mock notification dispatcher."""
from shared import new_id,utc_now
class NotificationDispatcher:
    def __init__(self,config=None): self.config=config or {}
    def send(self,channel:str,recipient:str,message:str,subject:str=None)->dict:
        return {"notification_id":new_id("notif"),"channel":channel,"recipient":recipient,
                "status":"DELIVERED","sent_at":utc_now(),"message_preview":message[:100]}
class DeduplicatorStore:
    _seen:dict={}
    def is_duplicate(self,recipient:str,event_type:str,window_minutes:int=60)->bool:
        key=f"{recipient}:{event_type}"
        import time; now=time.time()
        last=self._seen.get(key,0)
        if now-last < window_minutes*60: return True
        self._seen[key]=now; return False
