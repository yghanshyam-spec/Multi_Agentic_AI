"""agents/api_query/tools/http_client.py — mock HTTP client."""
from shared import new_id, utc_now
MOCK_SPEC={"openapi":"3.0.0","paths":{"/companies/{id}":{"get":{"summary":"Get company","parameters":[{"name":"id","in":"path","required":True}]}},"/companies/search":{"get":{"summary":"Search companies","parameters":[{"name":"name","in":"query"}]}}}}
class HTTPClient:
    def __init__(self,config=None): self.config=config or {}
    def get_spec(self,url=None): return MOCK_SPEC
    def request(self,method,path,params=None,headers=None,data=None):
        return {"status":200,"body":{"id":new_id("co"),"name":"Acme Corp","industry":"Technology",
            "revenue":"$50M","employees":250,"founded":2010},"headers":{"content-type":"application/json"},"retrieved_at":utc_now()}
