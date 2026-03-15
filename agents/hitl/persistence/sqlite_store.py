import sqlite3
import json
from typing import Dict, Any, Optional
from agent_hitl.persistence.storage import Storage

class SQLiteStore(Storage):
    def __init__(self, db_path: str = "hitl.db"):
        self.db_path = db_path
        self._conn = None
        self._init_db()

    def _get_conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                state TEXT
            )
        """)
        conn.commit()

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def save(self, run_id: str, state: Dict[str, Any]):
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO runs (run_id, state) VALUES (?, ?)",
            (run_id, json.dumps(state))
        )
        conn.commit()

    def load(self, run_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT state FROM runs WHERE run_id = ?", (run_id,))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None
