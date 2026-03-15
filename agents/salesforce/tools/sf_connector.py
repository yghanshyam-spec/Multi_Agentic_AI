"""agents/salesforce/tools/sf_connector.py — mock Salesforce connector."""
from shared import new_id,utc_now
class SalesforceConnector:
    def __init__(self,config=None): self.config=config or {}
    def query(self,soql:str)->dict:
        return {"totalSize":2,"done":True,"records":[
            {"Id":new_id("sf"),"Name":"Acme Corp","StageName":"Negotiation","Amount":85000,"CloseDate":"2025-03-31"},
            {"Id":new_id("sf"),"Name":"Globex Ltd","StageName":"Negotiation","Amount":120000,"CloseDate":"2025-02-28"}]}
    def create(self,sobject:str,data:dict)->dict:
        return {"id":new_id("sf"),"success":True,"errors":[],"sobject":sobject}
    def update(self,sobject:str,record_id:str,data:dict)->dict:
        return {"id":record_id,"success":True,"sobject":sobject}
