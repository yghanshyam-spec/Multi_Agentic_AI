"""agents/pdf_ingestor/prompts/defaults.py"""
CLASSIFY_SECTIONS = (
    "You are a document structure analyser.\n"
    "Identify the section headings and hierarchy in this document excerpt:\n{text_chunk}\n"
    "Return JSON: {{sections: [{{title: str, start_char: int, level: int}}]}}"
)
AUDIT_INGESTION = (
    "Summarise this PDF ingestion run for the audit log.\n"
    "File: {filename} | Chunks: {chunk_count} | Pages: {page_count} | Errors: {errors}\n"
    "Return JSON: {{summary: str, status: success|partial|failed, action_required: bool}}"
)
_REG={"pdf_classify_sections":CLASSIFY_SECTIONS,"pdf_audit":AUDIT_INGESTION}
def get_default_prompt(k): return _REG.get(k,"")
