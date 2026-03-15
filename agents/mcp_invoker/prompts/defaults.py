"""agents/mcp_invoker/prompts/defaults.py"""
SELECT_TOOL=("You have access to the following MCP tools:\n{tool_manifest}\nFor this task: {user_task}\nSelect the most appropriate tool and construct the input parameters.\nReturn JSON: {{tool_name: str, parameters: dict, rationale: str}}")
HANDLE_ERROR=("An MCP tool call failed.\nTool: {tool_name} | Error: {error}\nDetermine if the error is: parameter_invalid, server_unavailable, capability_missing, or unknown.\nSuggest corrective action and whether retry is appropriate.")
_REG={"mcp_select_tool":SELECT_TOOL,"mcp_handle_error":HANDLE_ERROR}
def get_default_prompt(k): return _REG.get(k,"")
