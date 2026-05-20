import sqlite3
from pathlib import Path

from auditx.domain.candidate import CandidateFindingRecord, CandidateProfile, CandidateScoreRecord


class InMemoryCandidateRepository:
    def __init__(self) -> None:
        self._profiles: dict[str, CandidateProfile] = {}
        self._scores: dict[str, CandidateScoreRecord] = {}
        self._findings: dict[str, CandidateFindingRecord] = {}

    def save_profile(self, profile: CandidateProfile) -> None:
        self._profiles[profile.candidate_id] = profile

    def get_profile(self, candidate_id: str) -> CandidateProfile | None:
        return self._profiles.get(candidate_id)

    def list_profiles(self) -> list[CandidateProfile]:
        return list(self._profiles.values())

    def save_score(self, score: CandidateScoreRecord) -> None:
        self._scores[score.score_id] = score

    def list_scores(self, candidate_id: str | None = None) -> list[CandidateScoreRecord]:
        scores = list(self._scores.values())
        if candidate_id is None:
            return scores
        return [score for score in scores if score.candidate_id == candidate_id]

    def top_scores(self, limit: int) -> list[CandidateScoreRecord]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        return sorted(self._scores.values(), key=self._score_sort_key)[:limit]

    def save_finding(self, finding: CandidateFindingRecord) -> None:
        self._findings[finding.finding_id] = finding

    def list_findings(self, candidate_id: str | None = None) -> list[CandidateFindingRecord]:
        findings = list(self._findings.values())
        if candidate_id is None:
            return findings
        return [finding for finding in findings if finding.candidate_id == candidate_id]

    def _score_sort_key(self, score: CandidateScoreRecord) -> tuple[float, int, float]:
        return (-score.total_score, score.risk_count, -score.created_at.timestamp())


class SQLiteCandidateRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def save_profile(self, profile: CandidateProfile) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO candidate_profiles (candidate_id, resume_id, payload)
                VALUES (?, ?, ?)
                ON CONFLICT(candidate_id) DO UPDATE SET
                    resume_id = excluded.resume_id,
                    payload = excluded.payload
                """,
                (profile.candidate_id, profile.resume_id, profile.model_dump_json()),
            )

    def get_profile(self, candidate_id: str) -> CandidateProfile | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM candidate_profiles WHERE candidate_id = ?",
                (candidate_id,),
            ).fetchone()
        if row is None:
            return None
        return CandidateProfile.model_validate_json(row[0])

    def list_profiles(self) -> list[CandidateProfile]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM candidate_profiles ORDER BY candidate_id"
            ).fetchall()
        return [CandidateProfile.model_validate_json(row[0]) for row in rows]

    def save_score(self, score: CandidateScoreRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO candidate_scores (
                    score_id, candidate_id, total_score, risk_count, created_at, payload
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(score_id) DO UPDATE SET
                    candidate_id = excluded.candidate_id,
                    total_score = excluded.total_score,
                    risk_count = excluded.risk_count,
                    created_at = excluded.created_at,
                    payload = excluded.payload
                """,
                (
                    score.score_id,
                    score.candidate_id,
                    score.total_score,
                    score.risk_count,
                    score.created_at.isoformat(),
                    score.model_dump_json(),
                ),
            )

    def list_scores(self, candidate_id: str | None = None) -> list[CandidateScoreRecord]:
        with self._connect() as connection:
            if candidate_id is None:
                rows = connection.execute(
                    "SELECT payload FROM candidate_scores ORDER BY created_at, score_id"
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT payload FROM candidate_scores
                    WHERE candidate_id = ?
                    ORDER BY created_at, score_id
                    """,
                    (candidate_id,),
                ).fetchall()
        return [CandidateScoreRecord.model_validate_json(row[0]) for row in rows]

    def top_scores(self, limit: int) -> list[CandidateScoreRecord]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT payload FROM candidate_scores
                ORDER BY total_score DESC, risk_count ASC, created_at DESC, score_id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [CandidateScoreRecord.model_validate_json(row[0]) for row in rows]

    def save_finding(self, finding: CandidateFindingRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO candidate_findings (finding_id, candidate_id, payload)
                VALUES (?, ?, ?)
                ON CONFLICT(finding_id) DO UPDATE SET
                    candidate_id = excluded.candidate_id,
                    payload = excluded.payload
                """,
                (finding.finding_id, finding.candidate_id, finding.model_dump_json()),
            )

    def list_findings(self, candidate_id: str | None = None) -> list[CandidateFindingRecord]:
        with self._connect() as connection:
            if candidate_id is None:
                rows = connection.execute(
                    "SELECT payload FROM candidate_findings ORDER BY finding_id"
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT payload FROM candidate_findings
                    WHERE candidate_id = ?
                    ORDER BY finding_id
                    """,
                    (candidate_id,),
                ).fetchall()
        return [CandidateFindingRecord.model_validate_json(row[0]) for row in rows]

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS candidate_profiles (
                    candidate_id TEXT PRIMARY KEY,
                    resume_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS candidate_scores (
                    score_id TEXT PRIMARY KEY,
                    candidate_id TEXT NOT NULL,
                    total_score REAL NOT NULL,
                    risk_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS candidate_findings (
                    finding_id TEXT PRIMARY KEY,
                    candidate_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)
