"""Tiny SQLite persistence layer for prep sessions (and the account tables).

Each session is one row. Large/nested parts (inputs, progress, generated
content, user progress, quiz attempts) are stored as JSON text columns so the
schema stays flexible while the content model evolves. Every session belongs to
the user who created it (user_id); account data lives in app/accounts.py.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

JSON_COLUMNS = ("inputs", "progress", "result", "user_state", "quiz_attempts", "warnings", "summary")
SCALAR_COLUMNS = ("user_id", "status", "mode", "company", "role", "years", "depth", "error")
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

CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,
    email           TEXT NOT NULL UNIQUE,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    password_hash   TEXT,
    google_sub      TEXT UNIQUE,
    avatar_url      TEXT,
    email_verified  INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    last_login_at   TEXT
);

CREATE TABLE IF NOT EXISTS auth_sessions (
    token_hash    TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at    TEXT NOT NULL,
    expires_at    TEXT NOT NULL,
    last_seen_at  TEXT NOT NULL,
    persistent    INTEGER NOT NULL DEFAULT 1,
    user_agent    TEXT,
    ip            TEXT
);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id);

CREATE TABLE IF NOT EXISTS password_resets (
    token_hash  TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL,
    expires_at  TEXT NOT NULL,
    used_at     TEXT
);

CREATE TABLE IF NOT EXISTS oauth_states (
    state_hash     TEXT PRIMARY KEY,
    code_verifier  TEXT NOT NULL,
    nonce          TEXT NOT NULL,
    next_path      TEXT,
    remember       INTEGER NOT NULL DEFAULT 1,
    created_at     TEXT NOT NULL,
    expires_at     TEXT NOT NULL
);
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
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.executescript(_SCHEMA)
            self._migrate()
            self._conn.commit()

    def _migrate(self) -> None:
        columns = {row["name"] for row in self._conn.execute("PRAGMA table_info(sessions)")}
        if "user_id" not in columns:  # databases created before accounts existed
            self._conn.execute("ALTER TABLE sessions ADD COLUMN user_id TEXT")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, created_at DESC)")

    # ------------------------------------------------------------- raw access
    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        """Run one write statement and commit; returns the affected row count."""
        with self._lock:
            cur = self._conn.execute(sql, params)
            self._conn.commit()
        return cur.rowcount

    def fetch_one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(sql, params).fetchone()
        return dict(row) if row is not None else None

    def fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

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

    def list(self, user_id: str, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, created_at, updated_at, status, mode, company, role, years, depth, error, summary "
                "FROM sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [self._decode(r) for r in rows]

    def adopt_unowned(self, user_id: str) -> int:
        """Give prep kits created before accounts existed to the given user."""
        return self.execute("UPDATE sessions SET user_id = ? WHERE user_id IS NULL", (user_id,))

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
