from datetime import datetime, timezone

from auditx.application.batch_review_service import BatchReviewService
from auditx.application.candidate_query_service import CandidateQueryService
from auditx.application.resume_library_service import ResumeLibraryService
from auditx.domain.batch import BatchCandidateStatus, BatchStatus
from auditx.domain.candidate import CandidateProfile, CandidateScoreRecord
from auditx.domain.resume_library import ResumeStatus
from auditx.domain.scoring import CandidateLayer
from auditx.infrastructure.storage.batch_repository import InMemoryBatchRepository
from auditx.infrastructure.storage.candidate_repository import InMemoryCandidateRepository
from auditx.infrastructure.storage.resume_repository import InMemoryResumeRepository


def test_resume_library_imports_metadata_without_document_payload() -> None:
    service = ResumeLibraryService(repository=InMemoryResumeRepository())

    resume = service.import_resume(
        resume_id="resume_1",
        filename="ada.pdf",
        parsed_document_artifact_uri="local://artifacts/jobs/job_1/parsed.json",
        imported_at=_now(),
    )

    assert resume.status == ResumeStatus.new
    assert resume.parsed_document_id == "local://artifacts/jobs/job_1/parsed.json"
    assert service.list_resumes(status=ResumeStatus.new) == [resume]


def test_candidate_query_service_filters_by_layer_and_returns_top_n() -> None:
    repository = InMemoryCandidateRepository()
    repository.save_profile(_profile("candidate_1", "Ada"))
    repository.save_profile(_profile("candidate_2", "Grace"))
    repository.save_score(_score("score_1", "candidate_1", 86, CandidateLayer.best, risk_count=0))
    repository.save_score(_score("score_2", "candidate_2", 61, CandidateLayer.potential, risk_count=0))
    service = CandidateQueryService(repository=repository)

    assert [item.profile.candidate_id for item in service.list_candidates(layer=CandidateLayer.best)] == [
        "candidate_1"
    ]
    assert [item.profile.candidate_id for item in service.top_n(limit=2)] == [
        "candidate_1",
        "candidate_2",
    ]


def test_batch_review_service_keeps_failed_candidate_isolated_from_batch() -> None:
    repository = InMemoryBatchRepository()
    service = BatchReviewService(repository=repository)
    batch = service.create_batch(
        batch_id="batch_1",
        name="Frontend Batch",
        job_template_id="frontend_engineer",
        created_at=_now(),
    )

    service.add_candidate(batch.batch_id, "candidate_1", created_at=_now())
    failed = service.mark_candidate_failed(
        batch_id=batch.batch_id,
        candidate_id="candidate_1",
        error="OCR failed",
        updated_at=_now(),
    )

    assert failed.status == BatchCandidateStatus.failed
    assert failed.error == "OCR failed"
    assert service.get_batch(batch.batch_id).status == BatchStatus.draft


def test_batch_review_service_reranks_candidates_and_records_top_n_reasons() -> None:
    batch_repository = InMemoryBatchRepository()
    candidate_repository = InMemoryCandidateRepository()
    candidate_repository.save_score(_score("score_1", "candidate_1", 92, CandidateLayer.best, risk_count=1))
    candidate_repository.save_score(_score("score_2", "candidate_2", 92, CandidateLayer.best, risk_count=0))
    candidate_repository.save_score(
        _score("score_3", "candidate_3", 70, CandidateLayer.potential, risk_count=0)
    )
    service = BatchReviewService(repository=batch_repository, candidate_repository=candidate_repository)
    batch = service.create_batch(
        batch_id="batch_1",
        name="Frontend Batch",
        job_template_id="frontend_engineer",
        created_at=_now(),
    )
    for candidate_id in ["candidate_1", "candidate_2", "candidate_3"]:
        service.add_candidate(batch.batch_id, candidate_id, created_at=_now())

    ranked = service.rerank(batch.batch_id, top_n=2, updated_at=_now())

    assert [candidate.candidate_id for candidate in ranked] == [
        "candidate_2",
        "candidate_1",
        "candidate_3",
    ]
    assert ranked[0].rank == 1
    assert ranked[0].status == BatchCandidateStatus.shortlisted
    assert ranked[0].score_id == "score_2"
    assert ranked[0].included_reason == "rank=1 score=92.0 risk_count=0"
    assert ranked[2].status == BatchCandidateStatus.eliminated
    assert ranked[2].eliminated_reason == "outside_top_2 rank=3 score=70.0 risk_count=0"
    assert service.get_batch(batch.batch_id).status == BatchStatus.completed


def _profile(candidate_id: str, display_name: str) -> CandidateProfile:
    return CandidateProfile(
        candidate_id=candidate_id,
        resume_id=f"resume_{candidate_id}",
        display_name=display_name,
        created_at=_now(),
        updated_at=_now(),
    )


def _score(
    score_id: str,
    candidate_id: str,
    total_score: float,
    layer: CandidateLayer,
    risk_count: int,
) -> CandidateScoreRecord:
    return CandidateScoreRecord(
        score_id=score_id,
        candidate_id=candidate_id,
        review_session_id=f"review_{candidate_id}",
        template_id="frontend_engineer",
        template_version="v1",
        total_score=total_score,
        layer=layer,
        risk_count=risk_count,
        created_at=_now(),
    )


def _now() -> datetime:
    return datetime(2026, 5, 20, tzinfo=timezone.utc)
