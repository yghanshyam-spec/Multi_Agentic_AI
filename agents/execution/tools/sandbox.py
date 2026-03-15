"""agents/execution/tools/sandbox.py — Docker sandbox abstraction (mock)."""
from shared import utc_now, new_id
def provision_sandbox() -> str:
    """Provision an isolated execution sandbox. Returns sandbox_id."""
    return new_id("sandbox")
def execute_script(script: str, sandbox_id: str) -> dict:
    """Execute script in sandbox. Returns execution output dict."""
    import time
    time.sleep(0.1)
    return {"script": script, "stdout": "CREATE INDEX\nINDEX created in 18.3s (8,200,000 rows)\nVACUUM: done",
            "stderr": "", "exit_code": 0, "duration_ms": 18300, "rows_affected": 8200000, "sandbox_id": sandbox_id}
