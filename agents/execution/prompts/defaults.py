"""agents/execution/prompts/defaults.py"""
PRECONDITIONS = "Review this execution step.\nStep: {step}\nEnvironment: {env_state}\nReturn JSON: {safe_to_execute: bool, blockers: [str], environment_ready: bool}"
VERIFY = "Verify the execution output.\nExpected: {expected}\nActual: {actual}\nReturn JSON: {success: bool, match_score: float, anomalies: [str], action: continue|retry|rollback}"
REPORT = "Summarise this execution run.\nDetails: {log}\nReturn JSON: {summary: str, status: str}"
_REGISTRY = {"execution_preconditions": PRECONDITIONS, "execution_verify": VERIFY, "execution_report": REPORT}
def get_default_prompt(key): return _REGISTRY.get(key, "")
