from datetime import datetime, timezone

from auditx.domain.batch import BatchCandidate, BatchCandidateStatus, BatchRecord, BatchStatus
from auditx.domain.candidate import CandidateProfile, CandidateScoreRecord
from auditx.domain.evidence_index import EvidenceIndexRecord
from auditx.domain.resume_library import ResumeRecord, ResumeStatus
from auditx.domain.scoring import CandidateLayer
from auditx.infrastructure.storage.batch_repository import InMemoryBatchRepository
from auditx.infrastructure.storage.candidate_repository import InMemoryCandidateRepository
from auditx.infrastructure.storage.evidence_repository import InMemoryEvidenceRepository
from auditx.infrastructure.storage.resume_repository import InMemoryResumeRepository


def test_resume_repository_saves_metadata_and_lists_by_status() -> None:
    repository = InMemoryResumeRepository()
    resume = ResumeRecord(
        resume_id="resume_1",
        filename="ada.pdf",
        imported_at=_now(),
        status=ResumeStatus.new,
        parsed_document_id="local://artifacts/jobs/job_1/parsed.json",
    )

    repository.save(resume)

    assert repository.get("resume_1") == resume
    assert repository.list(status=ResumeStatus.new) == [resume]
    assert repository.list(status=ResumeStatus.reviewed) == []


def test_candidate_repository_keeps_profiles_scores_and_top_n_queries_separate() -> None:
    repository = InMemoryCandidateRepository()
    profile = CandidateProfile(
        candidate_id="candidate_1",
        resume_id="resume_1",
        display_name="Ada Lovelace",
        source_document_artifact_uri="local://artifacts/jobs/job_1/source.pdf",
        created_at=_now(),
        updated_at=_now(),
    )
    weaker_profile = CandidateProfile(
        candidate_id="candidate_2",
        resume_id="resume_2",
        display_name="Grace Hopper",
        source_document_artifact_uri="local://artifacts/jobs/job_2/source.pdf",
        created_at=_now(),
        updated_at=_now(),
    )

    repository.save_profile(profile)
    repository.save_profile(weaker_profile)
    repository.save_score(_score("score_1", "candidate_1", 92, risk_count=0))
    repository.save_score(_score("score_2", "candidate_2", 92, risk_count=2))

    assert repository.get_profile("candidate_1") == profile
    assert repository.list_profiles() == [profile, weaker_profile]
    assert [score.candidate_id for score in repository.top_scores(limit=2)] == [
        "candidate_1",
        "candidate_2",
    ]


def test_evidence_repository_lists_by_candidate_without_returning_artifact_content() -> None:
    repository = InMemoryEvidenceRepository()
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

    repository.save(evidence)

    assert repository.list_by_candidate("candidate_1") == [evidence]
    assert repository.list_by_candidate("candidate_missing") == []


def test_batch_repository_tracks_batch_and_candidate_state_independently() -> None:
    repository = InMemoryBatchRepository()
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
        status=BatchCandidateStatus.pending,
        created_at=_now(),
        updated_at=_now(),
    )

    repository.save_batch(batch)
    repository.save_candidate(candidate)

    updated = candidate.model_copy(update={"status": BatchCandidateStatus.failed, "error": "OCR failed"})
    repository.save_candidate(updated)

    assert repository.get_batch("batch_1") == batch
    assert repository.list_candidates("batch_1") == [updated]
    assert repository.list_candidates("batch_missing") == []


def _score(score_id: str, candidate_id: str, total_score: float, risk_count: int) -> CandidateScoreRecord:
    return CandidateScoreRecord(
        score_id=score_id,
        candidate_id=candidate_id,
        review_session_id=f"review_{candidate_id}",
        template_id="frontend_engineer",
        template_version="v1",
        total_score=total_score,
        layer=CandidateLayer.best,
        dimension_scores={"ability_match": 90},
        risk_count=risk_count,
        created_at=_now(),
    )


def _now() -> datetime:
    return datetime(2026, 5, 20, tzinfo=timezone.utc)
