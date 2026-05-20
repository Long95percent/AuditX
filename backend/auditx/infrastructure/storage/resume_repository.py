import sqlite3
from pathlib import Path

from auditx.domain.resume_library import ResumeRecord, ResumeStatus


class InMemoryResumeRepository:
    def __init__(self) -> None:
        self._resumes: dict[str, ResumeRecord] = {}

    def save(self, resume: ResumeRecord) -> None:
        self._resumes[resume.resume_id] = resume

    def get(self, resume_id: str) -> ResumeRecord | None:
        return self._resumes.get(resume_id)

    def list(self, status: ResumeStatus | None = None) -> list[ResumeRecord]:
        resumes = list(self._resumes.values())
        if status is None:
            return resumes
        return [resume for resume in resumes if resume.status == status]


class SQLiteResumeRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def save(self, resume: ResumeRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO resumes (resume_id, status, imported_at, payload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(resume_id) DO UPDATE SET
                    status = excluded.status,
                    imported_at = excluded.imported_at,
                    payload = excluded.payload
                """,
                (
                    resume.resume_id,
                    resume.status.value,
                    resume.imported_at.isoformat(),
                    resume.model_dump_json(),
                ),
            )

    def get(self, resume_id: str) -> ResumeRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM resumes WHERE resume_id = ?",
                (resume_id,),
            ).fetchone()
        if row is None:
            return None
        return ResumeRecord.model_validate_json(row[0])

    def list(self, status: ResumeStatus | None = None) -> list[ResumeRecord]:
        with self._connect() as connection:
            if status is None:
                rows = connection.execute(
                    "SELECT payload FROM resumes ORDER BY imported_at, resume_id"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT payload FROM resumes WHERE status = ? ORDER BY imported_at, resume_id",
                    (status.value,),
                ).fetchall()
        return [ResumeRecord.model_validate_json(row[0]) for row in rows]

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS resumes (
                    resume_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    imported_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)
