import sqlite3
from pathlib import Path

from auditx.domain.evidence_index import EvidenceIndexRecord


class InMemoryEvidenceRepository:
    def __init__(self) -> None:
        self._evidence: dict[str, EvidenceIndexRecord] = {}

    def save(self, evidence: EvidenceIndexRecord) -> None:
        self._evidence[evidence.evidence_id] = evidence

    def get(self, evidence_id: str) -> EvidenceIndexRecord | None:
        return self._evidence.get(evidence_id)

    def list_by_candidate(self, candidate_id: str) -> list[EvidenceIndexRecord]:
        return [
            evidence
            for evidence in self._evidence.values()
            if evidence.candidate_id == candidate_id
        ]


class SQLiteEvidenceRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def save(self, evidence: EvidenceIndexRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO evidence_index (evidence_id, candidate_id, resume_id, payload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(evidence_id) DO UPDATE SET
                    candidate_id = excluded.candidate_id,
                    resume_id = excluded.resume_id,
                    payload = excluded.payload
                """,
                (
                    evidence.evidence_id,
                    evidence.candidate_id,
                    evidence.resume_id,
                    evidence.model_dump_json(),
                ),
            )

    def get(self, evidence_id: str) -> EvidenceIndexRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM evidence_index WHERE evidence_id = ?",
                (evidence_id,),
            ).fetchone()
        if row is None:
            return None
        return EvidenceIndexRecord.model_validate_json(row[0])

    def list_by_candidate(self, candidate_id: str) -> list[EvidenceIndexRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT payload FROM evidence_index
                WHERE candidate_id = ?
                ORDER BY evidence_id
                """,
                (candidate_id,),
            ).fetchall()
        return [EvidenceIndexRecord.model_validate_json(row[0]) for row in rows]

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_index (
                    evidence_id TEXT PRIMARY KEY,
                    candidate_id TEXT NOT NULL,
                    resume_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)
