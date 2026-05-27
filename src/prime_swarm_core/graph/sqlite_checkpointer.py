"""SQLite-backed checkpointer."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from prime_swarm_core.graph.state import RunState


class SQLiteCheckpointer:
    """Durable local checkpointer with append-only history."""

    schema_version = 1

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    async def get(self, run_id: str) -> RunState | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT state FROM checkpoints
                WHERE run_id = ?
                ORDER BY step_id DESC
                LIMIT 1
                """,
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return _state_from_payload(json.loads(row[0]))

    async def put(self, run_id: str, state: RunState) -> None:
        if run_id != state.run_id:
            raise ValueError("run_id must match state.run_id")
        payload = json.dumps(_state_to_payload(state), sort_keys=True)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(step_id), -1) + 1 FROM checkpoints WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            step_id = int(row[0])
            connection.execute(
                "INSERT INTO checkpoints (run_id, step_id, state) VALUES (?, ?, ?)",
                (run_id, step_id, payload),
            )
            connection.commit()

    async def list(self, run_id: str) -> list[RunState]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT state FROM checkpoints
                WHERE run_id = ?
                ORDER BY step_id ASC
                """,
                (run_id,),
            ).fetchall()
        return [_state_from_payload(json.loads(row[0])) for row in rows]

    async def delete(self, run_id: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM checkpoints WHERE run_id = ?", (run_id,))
            connection.commit()

    def get_schema_version(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT value FROM _meta WHERE key = 'schema_version'").fetchone()
        return int(row[0])

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS checkpoints (
                    run_id TEXT NOT NULL,
                    step_id INTEGER NOT NULL,
                    state JSON NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (run_id, step_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS _meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "INSERT OR IGNORE INTO _meta (key, value) VALUES ('schema_version', ?)",
                (str(self.schema_version),),
            )
            connection.commit()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        try:
            yield connection
        finally:
            connection.close()


def _state_to_payload(state: RunState) -> dict[str, Any]:
    return {
        "run_id": state.run_id,
        "values": state.values,
        "current_node": state.current_node,
        "status": state.status,
        "created_at": state.created_at.isoformat(),
        "updated_at": state.updated_at.isoformat(),
    }


def _state_from_payload(payload: dict[str, Any]) -> RunState:
    return RunState(
        run_id=payload["run_id"],
        values=payload.get("values", {}),
        current_node=payload.get("current_node"),
        status=payload.get("status", "running"),
        created_at=datetime.fromisoformat(payload["created_at"]),
        updated_at=datetime.fromisoformat(payload["updated_at"]),
    )
