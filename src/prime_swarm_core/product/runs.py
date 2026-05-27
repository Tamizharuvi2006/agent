"""Research run records and persistence boundary."""

from __future__ import annotations

from copy import deepcopy
from contextlib import closing
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Protocol


RunStatus = str


@dataclass(frozen=True, slots=True)
class RunRecord:
    run_id: str
    question: str
    status: RunStatus
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "question": self.question,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class RunStore(Protocol):
    async def put(self, record: RunRecord) -> None: ...

    async def get(self, run_id: str) -> RunRecord | None: ...


class InMemoryRunStore:
    """Local run store used until Postgres is selected and wired."""

    def __init__(self) -> None:
        self._records: dict[str, RunRecord] = {}

    async def put(self, record: RunRecord) -> None:
        self._records[record.run_id] = deepcopy(record)

    async def get(self, run_id: str) -> RunRecord | None:
        record = self._records.get(run_id)
        return deepcopy(record) if record else None


class SQLiteRunStore:
    """SQLite-backed run store for local durable product runs."""

    schema_version = "1"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if self.path != Path(":memory:"):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS _meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                INSERT OR REPLACE INTO _meta (key, value)
                VALUES ('schema_version', ?)
                """,
                (self.schema_version,),
            )
            connection.commit()

    async def put(self, record: RunRecord) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO runs (
                    run_id,
                    question,
                    status,
                    result_json,
                    error,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.run_id,
                    record.question,
                    record.status,
                    json.dumps(record.result, sort_keys=True),
                    record.error,
                    record.created_at.isoformat(),
                    record.updated_at.isoformat(),
                ),
            )
            connection.commit()

    async def get(self, run_id: str) -> RunRecord | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT run_id, question, status, result_json, error, created_at, updated_at
                FROM runs
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()
        return self._record_from_row(row) if row else None

    async def list(self) -> list[RunRecord]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT run_id, question, status, result_json, error, created_at, updated_at
                FROM runs
                ORDER BY created_at ASC
                """
            ).fetchall()
        return [self._record_from_row(row) for row in rows]

    async def delete(self, run_id: str) -> None:
        with closing(self._connect()) as connection:
            connection.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
            connection.commit()

    def schema(self) -> str | None:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT value FROM _meta WHERE key = 'schema_version'").fetchone()
        return str(row["value"]) if row else None

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    @classmethod
    def _record_from_row(cls, row: sqlite3.Row) -> RunRecord:
        return RunRecord(
            run_id=str(row["run_id"]),
            question=str(row["question"]),
            status=str(row["status"]),
            result=json.loads(str(row["result_json"])),
            error=row["error"],
            created_at=cls._parse_datetime(str(row["created_at"])),
            updated_at=cls._parse_datetime(str(row["updated_at"])),
        )
