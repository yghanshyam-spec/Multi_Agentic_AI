"""agents/sql/tools/db_connector.py — mock DB connector."""
from shared import new_id, utc_now

class DBConnector:
    def __init__(self, config=None):
        self.config = config or {}
        self.dialect = config.get("dialect", "postgresql")

    def get_schema(self, tables=None) -> dict:
        return {"orders": {"id": "bigint", "created_at": "timestamp",
                           "status": "varchar", "total": "numeric", "region": "varchar"},
                "customers": {"id": "bigint", "name": "varchar", "email": "varchar"}}

    def execute(self, sql: str) -> dict:
        return {"rows": [{"region": "APAC", "revenue": 1_240_000},
                         {"region": "EMEA", "revenue": 2_100_000}],
                "row_count": 2, "query_time_ms": 42, "executed_at": utc_now()}
