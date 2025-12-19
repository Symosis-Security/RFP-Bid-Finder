import json
import sqlite3
import time
from typing import Any, Dict, Optional


def _now_ts() -> int:
    return int(time.time())


class SimpleCache:
    def __init__(self, path: str):
        self.path = path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.path) as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    k TEXT PRIMARY KEY,
                    created_at INTEGER NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            con.commit()

    def get(self, key: str, ttl_seconds: int) -> Optional[Dict[str, Any]]:
        if ttl_seconds <= 0:
            return None
        with sqlite3.connect(self.path) as con:
            row = con.execute("SELECT created_at, payload FROM cache WHERE k=?", (key,)).fetchone()
            if not row:
                return None
            created_at, payload = row
            if _now_ts() - int(created_at) > ttl_seconds:
                return None
            try:
                return json.loads(payload)
            except Exception:
                return None

    def set(self, key: str, payload: Dict[str, Any]) -> None:
        with sqlite3.connect(self.path) as con:
            con.execute(
                "INSERT OR REPLACE INTO cache (k, created_at, payload) VALUES (?, ?, ?)",
                (key, _now_ts(), json.dumps(payload)),
            )
            con.commit()
