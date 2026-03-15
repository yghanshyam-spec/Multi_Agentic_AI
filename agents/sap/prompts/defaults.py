"""agents/sap/prompts/defaults.py"""
PARSE_SAP_INTENT=("Parse this SAP-related business request.\nRequest: {user_request}\nIdentify: sap_module (MM/SD/FI/HR), operation (query/post/update), bapi_hint, key_fields (PO number, vendor, material, cost centre).\nReturn structured JSON.")
SELECT_BAPI=("Select the most appropriate SAP BAPI or OData service for this operation.\nModule: {sap_module} | Operation: {operation} | Key fields: {key_fields}\nAvailable BAPIs: {bapi_catalogue}\nReturn JSON: {{bapi_name: str, import_params: dict, rationale: str}}")
HANDLE_SAP_EXCEPTION=("A SAP BAPI returned an error message.\nBAPI: {bapi_name} | Error message: {sap_error}\nDiagnose the likely cause and suggest: retry_possible (bool), user_action_needed (str), escalate_to_human (bool).")
TRANSFORM_SAP_DATA=("Convert SAP technical data to business-friendly format.\nData: {sap_data}\nConversions: YYYYMMDD dates → DD/MM/YYYY, CURR fields ÷ 100, unit codes → full names.\nReturn JSON: {{transformed: dict, changes: [str]}}")
SUMMARISE_SAP_RESPONSE=("Summarise this SAP transaction result for a business user.\nOperation: {operation} | SAP result: {sap_data}\nProvide a clear, jargon-free summary. Include document number, status, and any action items.")
_REG={"sap_parse_intent":PARSE_SAP_INTENT,"sap_select_bapi":SELECT_BAPI,"sap_handle_exception":HANDLE_SAP_EXCEPTION,
      "sap_transform_data":TRANSFORM_SAP_DATA,"sap_summarise_response":SUMMARISE_SAP_RESPONSE}
def get_default_prompt(k): return _REG.get(k,"")
