import sqlite3
from pathlib import Path
from typing import Protocol

from auditx.application.audit_job_service import AuditJob


class AuditJobRepository(Protocol):
    def save(self, job: AuditJob) -> None:
        pass

    def get(self, job_id: str) -> AuditJob | None:
        pass


class SQLiteAuditJobRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def save(self, job: AuditJob) -> None:
        payload = job.model_dump_json()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO audit_jobs (job_id, payload)
                VALUES (?, ?)
                ON CONFLICT(job_id) DO UPDATE SET payload = excluded.payload
                """,
                (job.job_id, payload),
            )

    def get(self, job_id: str) -> AuditJob | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM audit_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return AuditJob.model_validate_json(row[0])

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_jobs (
                    job_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)