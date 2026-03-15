"""agents/audit/tools/audit_store.py — Append-only audit log store (mock)."""
import json
from shared import utc_now, new_id
_LOG = []
def persist(events: list) -> list:
    records = [{"record_id": new_id("audit"), "stored_at": utc_now(), **e} for e in events]
    _LOG.extend(records)
    return records
def get_all(): return list(_LOG)
