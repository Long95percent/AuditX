import sqlite3
from pathlib import Path

from auditx.domain.batch import BatchCandidate, BatchRecord


class InMemoryBatchRepository:
    def __init__(self) -> None:
        self._batches: dict[str, BatchRecord] = {}
        self._candidates: dict[tuple[str, str], BatchCandidate] = {}

    def save_batch(self, batch: BatchRecord) -> None:
        self._batches[batch.batch_id] = batch

    def get_batch(self, batch_id: str) -> BatchRecord | None:
        return self._batches.get(batch_id)

    def list_batches(self) -> list[BatchRecord]:
        return list(self._batches.values())

    def save_candidate(self, candidate: BatchCandidate) -> None:
        self._candidates[(candidate.batch_id, candidate.candidate_id)] = candidate

    def get_candidate(self, batch_id: str, candidate_id: str) -> BatchCandidate | None:
        return self._candidates.get((batch_id, candidate_id))

    def list_candidates(self, batch_id: str) -> list[BatchCandidate]:
        return [
            candidate
            for candidate in self._candidates.values()
            if candidate.batch_id == batch_id
        ]


class SQLiteBatchRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def save_batch(self, batch: BatchRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO batches (batch_id, status, created_at, payload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(batch_id) DO UPDATE SET
                    status = excluded.status,
                    created_at = excluded.created_at,
                    payload = excluded.payload
                """,
                (
                    batch.batch_id,
                    batch.status.value,
                    batch.created_at.isoformat(),
                    batch.model_dump_json(),
                ),
            )

    def get_batch(self, batch_id: str) -> BatchRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM batches WHERE batch_id = ?",
                (batch_id,),
            ).fetchone()
        if row is None:
            return None
        return BatchRecord.model_validate_json(row[0])

    def list_batches(self) -> list[BatchRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM batches ORDER BY created_at, batch_id"
            ).fetchall()
        return [BatchRecord.model_validate_json(row[0]) for row in rows]

    def save_candidate(self, candidate: BatchCandidate) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO batch_candidates (batch_id, candidate_id, status, payload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(batch_id, candidate_id) DO UPDATE SET
                    status = excluded.status,
                    payload = excluded.payload
                """,
                (
                    candidate.batch_id,
                    candidate.candidate_id,
                    candidate.status.value,
                    candidate.model_dump_json(),
                ),
            )

    def get_candidate(self, batch_id: str, candidate_id: str) -> BatchCandidate | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT payload FROM batch_candidates
                WHERE batch_id = ? AND candidate_id = ?
                """,
                (batch_id, candidate_id),
            ).fetchone()
        if row is None:
            return None
        return BatchCandidate.model_validate_json(row[0])

    def list_candidates(self, batch_id: str) -> list[BatchCandidate]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT payload FROM batch_candidates
                WHERE batch_id = ?
                ORDER BY candidate_id
                """,
                (batch_id,),
            ).fetchall()
        return [BatchCandidate.model_validate_json(row[0]) for row in rows]

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS batches (
                    batch_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS batch_candidates (
                    batch_id TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (batch_id, candidate_id)
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)
