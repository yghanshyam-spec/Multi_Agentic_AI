"""agents/mcp_invoker/tools/mcp_client.py — mock MCP client."""
from shared import new_id,utc_now
class MCPClient:
    def __init__(self,config=None): self.config=config or {}
    def get_registry(self)->list:
        return [{"server_id":"web_search","url":"stdio://mcp-web-search","auth":"none"},
                {"server_id":"code_exec","url":"http://localhost:3001","auth":"api_key"}]
    def negotiate(self,server_id:str)->dict:
        return {"tools":[{"name":"web_search","description":"Search the web","input_schema":{"query":"str"}},
                         {"name":"run_python","description":"Execute Python code","input_schema":{"code":"str"}}]}
    def call(self,server_id:str,tool_name:str,params:dict)->dict:
        return {"request_id":new_id("mcp"),"tool":tool_name,"result":f"Mock result for {tool_name}({params})","status":"success","ts":utc_now()}
