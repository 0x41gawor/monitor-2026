# app/run_log.py
from __future__ import annotations

import logging
import os
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date    TEXT NOT NULL,
    trigger     TEXT NOT NULL,
    status      TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    duration_s  REAL,
    error       TEXT
)
"""

MAX_ERROR_LENGTH = 500


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RunLog:
    """
    History of monitor runs (scheduler / manual / cli).
    Logging must never break a run, so write failures are only logged.
    """

    def __init__(self, path: str):
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute(SCHEMA)
        return conn

    def start(self, run_date: str, trigger: str) -> int | None:
        try:
            with closing(self._connect()) as conn, conn:
                cursor = conn.execute(
                    "INSERT INTO runs (run_date, trigger, status, started_at) "
                    "VALUES (?, ?, 'running', ?)",
                    (run_date, trigger, _now()),
                )
                return cursor.lastrowid
        except Exception:
            logger.warning("Could not write run log (start)", exc_info=True)
            return None

    def finish(self, run_id: int | None, status: str, started: float, error: str | None = None) -> None:
        if run_id is None:
            return

        try:
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    "UPDATE runs SET status = ?, finished_at = ?, duration_s = ?, error = ? "
                    "WHERE id = ?",
                    (
                        status,
                        _now(),
                        round(time.monotonic() - started, 1),
                        error[:MAX_ERROR_LENGTH] if error else None,
                        run_id,
                    ),
                )
        except Exception:
            logger.warning("Could not write run log (finish)", exc_info=True)

    def close_stale(self) -> None:
        """
        Runs left in 'running' by a container that stopped mid-run.
        """
        try:
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    "UPDATE runs SET status = 'fail', finished_at = ?, error = 'interrupted' "
                    "WHERE status = 'running'",
                    (_now(),),
                )
        except Exception:
            logger.warning("Could not close stale runs", exc_info=True)

    def recent(self, limit: int = 20) -> list[dict]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM runs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
