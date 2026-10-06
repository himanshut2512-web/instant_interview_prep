"""Tiny SQLite persistence layer for prep sessions.

Each session is one row. Large/nested parts (inputs, progress, generated
content, user progress, quiz attempts) are stored as JSON text columns so the
schema stays flexible while the content model evolves.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

JSON_COLUMNS = ("inputs", "progress", "result", "user_state", "quiz_attempts", "warnings", "summary")
SCALAR_COLUMNS = ("status", "mode", "company", "role", "years", "depth", "error")
ALL_COLUMNS = SCALAR_COLUMNS + JSON_COLUMNS

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id            TEXT PRIMARY KEY,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    status        TEXT NOT NULL,
    mode          TEXT NOT NULL,
    company       TEXT NOT NULL,
    role          TEXT,
    years         REAL,
    depth         TEXT,
    error         TEXT,
    inputs        TEXT,
    progress      TEXT,
    result        TEXT,
    user_state    TEXT,
    quiz_attempts TEXT,
    warnings      TEXT,
    summary       TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at DESC);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, db_path: Path | str):
        path = Path(db_path)
        if str(path) != ":memory:":
            path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            if str(path) != ":memory:":
                self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _encode(column: str, value: Any) -> Any:
        if column in JSON_COLUMNS:
            return json.dumps(value, ensure_ascii=False) if value is not None else None
        return value

    @staticmethod
    def _decode(row: sqlite3.Row, columns: tuple[str, ...] | None = None) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for key in row.keys():
            if columns is not None and key not in columns:
                continue
            value = row[key]
            if key in JSON_COLUMNS and value is not None:
                value = json.loads(value)
            data[key] = value
        return data

    # ------------------------------------------------------------------- CRUD
    def create(self, session_id: str, **fields: Any) -> dict[str, Any]:
        now = utcnow()
        values = {c: self._encode(c, fields.get(c)) for c in ALL_COLUMNS}
        with self._lock:
            self._conn.execute(
                f"INSERT INTO sessions (id, created_at, updated_at, {', '.join(ALL_COLUMNS)}) "
                f"VALUES (?, ?, ?, {', '.join('?' for _ in ALL_COLUMNS)})",
                (session_id, now, now, *values.values()),
            )
            self._conn.commit()
        created = self.get(session_id)
        assert created is not None
        return created

    def get(self, session_id: str, columns: tuple[str, ...] | None = None) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            return None
        keep = None if columns is None else ("id", "created_at", "updated_at", *columns)
        return self._decode(row, keep)

    def update(self, session_id: str, **fields: Any) -> None:
        unknown = set(fields) - set(ALL_COLUMNS)
        if unknown:
            raise ValueError(f"Unknown session fields: {sorted(unknown)}")
        if not fields:
            return
        assignments = ", ".join(f"{c} = ?" for c in fields)
        params = [self._encode(c, v) for c, v in fields.items()]
        with self._lock:
            self._conn.execute(
                f"UPDATE sessions SET {assignments}, updated_at = ? WHERE id = ?",
                (*params, utcnow(), session_id),
            )
            self._conn.commit()

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, created_at, updated_at, status, mode, company, role, years, depth, error, summary "
                "FROM sessions ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._decode(r) for r in rows]

    def delete(self, session_id: str) -> bool:
        with self._lock:
            cur = self._conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            self._conn.commit()
        return cur.rowcount > 0

    def mark_interrupted(self) -> int:
        """Sessions left 'running' by a crash/restart can never finish - flag them."""
        with self._lock:
            cur = self._conn.execute(
                "UPDATE sessions SET status = 'failed', error = ?, updated_at = ? "
                "WHERE status IN ('queued', 'running')",
                ("The server restarted while this prep kit was being generated. Use Retry to run it again.", utcnow()),
            )
            self._conn.commit()
        return cur.rowcount

    def close(self) -> None:
        with self._lock:
            self._conn.close()
