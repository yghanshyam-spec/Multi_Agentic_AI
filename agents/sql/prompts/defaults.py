"""agents/sql/prompts/defaults.py"""

GENERATE_SQL = (
    "You are an expert SQL engineer for {dialect} databases.\n"
    "Given schema:\n{schema}\n"
    "Generate a safe, read-only SQL query for:\n{user_request}\n"
    "Return ONLY the SQL statement."
)
VALIDATE_SQL = (
    "You are a SQL safety reviewer.\n"
    "Review the SQL below for: injection risks, non-SELECT statements, "
    "missing WHERE clauses on large tables.\n"
    "SQL: {sql}\n"
    "Return JSON: {{valid: bool, issues: [str], safe_to_execute: bool}}"
)
CORRECT_SQL = (
    "You are an expert SQL debugger.\n"
    "Original query: {sql}\nDatabase error: {error}\nSchema: {schema}\n"
    "Fix the query. Return ONLY corrected SQL."
)
FORMAT_OUTPUT = (
    "You are a data analyst assistant.\n"
    "Present these query results clearly for a business user:\n{results}\n"
    "Query answered: {user_request}\n"
    "Include summary and key observations."
)

_REG = {
    "sql_generate": GENERATE_SQL, "sql_validate": VALIDATE_SQL,
    "sql_correct": CORRECT_SQL, "sql_format": FORMAT_OUTPUT,
}
def get_default_prompt(k): return _REG.get(k, "")
