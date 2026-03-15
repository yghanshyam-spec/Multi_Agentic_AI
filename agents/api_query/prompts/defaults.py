"""agents/api_query/prompts/defaults.py"""
SELECT_ENDPOINT=("You are an API integration assistant.\nGiven this user intent and the available API endpoints below, identify the most appropriate endpoint.\nIntent: {user_intent}\nAvailable endpoints: {endpoint_catalogue}\nReturn JSON: {{endpoint_path: str, method: str, rationale: str, parameters_needed: [str]}}")
BUILD_PARAMETERS=("Construct the request parameters for this API call.\nEndpoint schema: {param_schema}\nUser intent: {user_intent}\nExtracted entities: {entities}\nReturn JSON matching the endpoint's required parameter schema exactly.")
PARSE_RESPONSE=("Parse and normalise this API response for downstream agent consumption.\nRaw response: {raw_response}\nExpected data type: {expected_type}\nExtract key fields, flag null/error values, return clean JSON.")
HANDLE_ERROR=("An API call returned an error. Diagnose and suggest a corrective action.\nError: {error_response}\nOriginal request: {request}\nReturn JSON: {{error_type, retry_possible: bool, corrective_action: str}}")
_REG={"api_select_endpoint":SELECT_ENDPOINT,"api_build_params":BUILD_PARAMETERS,"api_parse_response":PARSE_RESPONSE,"api_handle_error":HANDLE_ERROR}
def get_default_prompt(k): return _REG.get(k,"")
