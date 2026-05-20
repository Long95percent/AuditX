from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from auditx.domain.batch import BatchCandidate, BatchCandidateStatus, BatchRecord, BatchStatus
from auditx.domain.candidate import CandidateProfile, CandidateScoreRecord
from auditx.domain.evidence_index import EvidenceIndexRecord
from auditx.domain.resume_library import ResumeRecord, ResumeStatus
from auditx.domain.scoring import CandidateLayer
from auditx.infrastructure.storage.batch_repository import SQLiteBatchRepository
from auditx.infrastructure.storage.candidate_repository import SQLiteCandidateRepository
from auditx.infrastructure.storage.evidence_repository import SQLiteEvidenceRepository
from auditx.infrastructure.storage.resume_repository import SQLiteResumeRepository


def test_sqlite_resume_repository_persists_across_instances() -> None:
    database_path = _database_path()
    resume = ResumeRecord(
        resume_id="resume_1",
        filename="ada.pdf",
        imported_at=_now(),
        status=ResumeStatus.new,
        parsed_document_id="local://artifacts/jobs/job_1/parsed.json",
    )

    SQLiteResumeRepository(database_path).save(resume)
    loaded_repository = SQLiteResumeRepository(database_path)

    assert loaded_repository.get("resume_1") == resume
    assert loaded_repository.list(status=ResumeStatus.new) == [resume]


def test_sqlite_candidate_repository_persists_profiles_scores_and_findings() -> None:
    database_path = _database_path()
    repository = SQLiteCandidateRepository(database_path)
    profile = CandidateProfile(
        candidate_id="candidate_1",
        resume_id="resume_1",
        display_name="Ada Lovelace",
        source_document_artifact_uri="local://artifacts/jobs/job_1/source.pdf",
        created_at=_now(),
        updated_at=_now(),
    )
    score = CandidateScoreRecord(
        score_id="score_1",
        candidate_id="candidate_1",
        review_session_id="review_1",
        template_id="frontend_engineer",
        template_version="v1",
        total_score=93,
        layer=CandidateLayer.best,
        risk_count=0,
        created_at=_now(),
    )

    repository.save_profile(profile)
    repository.save_score(score)
    loaded_repository = SQLiteCandidateRepository(database_path)

    assert loaded_repository.get_profile("candidate_1") == profile
    assert loaded_repository.list_scores(candidate_id="candidate_1") == [score]
    assert loaded_repository.top_scores(limit=1) == [score]


def test_sqlite_evidence_repository_persists_lightweight_index() -> None:
    database_path = _database_path()
    evidence = EvidenceIndexRecord(
        evidence_id="evidence_1",
        candidate_id="candidate_1",
        resume_id="resume_1",
        parsed_document_artifact_uri="local://artifacts/jobs/job_1/parsed.json",
        page_number=1,
        block_id="block_1",
        text_excerpt="React TypeScript",
        created_at=_now(),
    )

    SQLiteEvidenceRepository(database_path).save(evidence)
    loaded_repository = SQLiteEvidenceRepository(database_path)

    assert loaded_repository.get("evidence_1") == evidence
    assert loaded_repository.list_by_candidate("candidate_1") == [evidence]


def test_sqlite_batch_repository_persists_batch_and_candidate_state() -> None:
    database_path = _database_path()
    repository = SQLiteBatchRepository(database_path)
    batch = BatchRecord(
        batch_id="batch_1",
        name="Frontend Batch",
        status=BatchStatus.draft,
        job_template_id="frontend_engineer",
        created_at=_now(),
        updated_at=_now(),
    )
    candidate = BatchCandidate(
        batch_id="batch_1",
        candidate_id="candidate_1",
        status=BatchCandidateStatus.failed,
        error="OCR failed",
        created_at=_now(),
        updated_at=_now(),
    )

    repository.save_batch(batch)
    repository.save_candidate(candidate)
    loaded_repository = SQLiteBatchRepository(database_path)

    assert loaded_repository.get_batch("batch_1") == batch
    assert loaded_repository.list_candidates("batch_1") == [candidate]


def _database_path() -> Path:
    directory = Path("backend/tests/.repo_tmp")
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"batch_system_{uuid4().hex}.sqlite3"


def _now() -> datetime:
    return datetime(2026, 5, 20, tzinfo=timezone.utc)
