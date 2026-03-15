"""agents/salesforce/prompts/defaults.py"""
PARSE_SF_INTENT=("Parse this Salesforce-related request into a structured operation.\nRequest: {user_request}\nExtract: operation_type (query/create/update/delete), object_type (Lead/Opportunity/Account/Contact/Case), filters, fields_needed.\nReturn JSON.")
GENERATE_SOQL=("Generate a Salesforce SOQL query.\nObject: {sf_object} | Fields needed: {fields} | Filters: {filters}\nRules: always include Id field, use LIMIT for large objects, avoid wildcard SELECT.\nReturn only the SOQL string.")
VALIDATE_RECORDS=("Validate these Salesforce records before a write operation.\nRecords to write: {records}\nValidation rules: {validation_rules}\nCheck required fields, data types, relationship IDs.\nReturn JSON: {{valid: bool, invalid_records: [str], issues: [str]}}")
ENRICH_DATA=("Enrich this Salesforce record with third-party data.\nRecord: {record}\nEnrichment sources: {sources}\nReturn JSON: {{enriched_record: dict, fields_added: [str]}}")
FORMAT_SF_RESPONSE=("Format this Salesforce query result for a business user.\nRaw results: {sf_results} | Original request: {user_request}\nPresent as a clear, business-friendly summary. Include record counts, key fields, and any notable patterns.")
LOG_SF_OPERATION=("Log this Salesforce operation for audit trail.\nOperation: {operation_type} | Object: {sf_object} | Records affected: {record_count}\nReturn JSON: {{audit_entry: dict, compliance_flags: [str]}}")
_REG={"sf_parse_intent":PARSE_SF_INTENT,"sf_generate_soql":GENERATE_SOQL,"sf_validate_records":VALIDATE_RECORDS,
      "sf_enrich_data":ENRICH_DATA,"sf_format_response":FORMAT_SF_RESPONSE,"sf_log_operation":LOG_SF_OPERATION}
def get_default_prompt(k): return _REG.get(k,"")
