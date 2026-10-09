"""Persistencia editorial: PostgreSQL externo o SQLite local.

Nunca mezclar la base analítica (que se reconstruye desde el snapshot)
con decisiones humanas o borradores guardados.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3

KEYS = ("case_id", "action", "state", "reviewer", "note", "updated_at")


class EditorialStore:
    def __init__(self, dsn: str | None = None):
        self.dsn = dsn if dsn is not None else os.environ.get("EDITORIAL_DATABASE_URL", "sqlite:///data/editorial.sqlite3")
        self.postgres = self.dsn.startswith(("postgres://", "postgresql://"))
        if not self.postgres and not self.dsn.startswith("sqlite:///"):
            raise ValueError("EDITORIAL_DATABASE_URL debe comenzar con postgresql:// o sqlite:///")
        if not self.postgres:
            self.path = Path(self.dsn[len("sqlite:///"):])
            self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self):
        if self.postgres:
            try:
                import psycopg
            except ImportError as exc:
                raise RuntimeError("Instala psycopg[binary] para PostgreSQL") from exc
            # psycopg ejecuta COMMIT cuando se cierra normalmente el bloque
            with psycopg.connect(self.dsn, connect_timeout=10) as conn:
                yield conn
        else:
            with sqlite3.connect(str(self.path), timeout=20) as conn:
                yield conn

    def _sql(self, query: str) -> str:
        return query.replace("?", "%s") if self.postgres else query

    def _initialize(self, conn):
        conn.execute("""CREATE TABLE IF NOT EXISTS editorial_reviews (
            case_id TEXT PRIMARY KEY, action TEXT NOT NULL, state TEXT NOT NULL,
            reviewer TEXT NOT NULL, note TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS editorial_drafts (
            case_id TEXT NOT NULL, mode TEXT NOT NULL,
            fingerprint TEXT NOT NULL, payload TEXT NOT NULL,
            updated_at TEXT NOT NULL, PRIMARY KEY(case_id, mode)
        )""")

    def all_reviews(self) -> dict[str, dict]:
        with self.connection() as conn:
            self._initialize(conn)
            rows = conn.execute("SELECT case_id, action, state, reviewer, note, updated_at FROM editorial_reviews").fetchall()
        return {str(r[0]): dict(zip(KEYS, r)) for r in rows}

    def get_review(self, case_id: str) -> dict | None:
        with self.connection() as conn:
            self._initialize(conn)
            row = conn.execute(self._sql("SELECT case_id, action, state, reviewer, note, updated_at FROM editorial_reviews WHERE case_id=?"), (case_id,)).fetchone()
        return dict(zip(KEYS, row)) if row else None

    def save_review(self, case_id: str, action: str, state: str, reviewer: str, note: str, updated_at: str) -> dict:
        with self.connection() as conn:
            self._initialize(conn)
            conn.execute(self._sql("""INSERT INTO editorial_reviews(case_id, action, state, reviewer, note, updated_at)
              VALUES(?,?,?,?,?,?) ON CONFLICT(case_id) DO UPDATE SET
              action=excluded.action, state=excluded.state, reviewer=excluded.reviewer,
              note=excluded.note, updated_at=excluded.updated_at"""),
              (case_id, action, state, reviewer, note, updated_at))
        return self.get_review(case_id) or {}

    def save_draft(self, case_id: str, mode: str, fingerprint: str, payload: dict) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.connection() as conn:
            self._initialize(conn)
            conn.execute(self._sql("""INSERT INTO editorial_drafts(case_id,mode,fingerprint,payload,updated_at)
             VALUES(?,?,?,?,?) ON CONFLICT(case_id,mode) DO UPDATE SET
             fingerprint=excluded.fingerprint, payload=excluded.payload, updated_at=excluded.updated_at"""),
             (case_id, mode, fingerprint, json.dumps(payload, ensure_ascii=False), now))

    def get_draft(self, case_id: str, mode: str, fingerprint: str) -> dict | None:
        with self.connection() as conn:
            self._initialize(conn)
            row = conn.execute(self._sql("SELECT payload, fingerprint FROM editorial_drafts WHERE case_id=? AND mode=?"), (case_id, mode)).fetchone()
        if not row or row[1] != fingerprint:
            return None
        data = json.loads(row[0]); return data if isinstance(data, dict) else None
