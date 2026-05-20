from datetime import datetime, timezone

from auditx.application.audit_job_service import AuditJob, AuditJobStatus
from auditx.application.review_result_indexer import ReviewResultIndexer
from auditx.domain.artifacts import ArtifactRef
from auditx.domain.audit import AuditFinding, Evidence, RiskLevel
from auditx.domain.documents import BBox
from auditx.domain.evidence_index import EvidenceIndexRecord
from auditx.domain.scoring import CandidateLayer, ScoreResult
from auditx.infrastructure.storage.candidate_repository import InMemoryCandidateRepository
from auditx.infrastructure.storage.evidence_repository import InMemoryEvidenceRepository
from auditx.infrastructure.storage.resume_repository import InMemoryResumeRepository


def test_review_result_indexer_projects_completed_job_into_query_tables() -> None:
    resume_repository = InMemoryResumeRepository()
    candidate_repository = InMemoryCandidateRepository()
    evidence_repository = InMemoryEvidenceRepository()
    indexer = ReviewResultIndexer(
        resume_repository=resume_repository,
        candidate_repository=candidate_repository,
        evidence_repository=evidence_repository,
    )
    job = AuditJob(
        job_id="job_1",
        file_path="ada.pdf",
        status=AuditJobStatus.completed,
        document_id="doc_1",
        findings=[_finding()],
        score=_score(),
        artifacts=[
            _artifact("source_document", "local://artifacts/jobs/job_1/source.pdf"),
            _artifact("parsed_document", "local://artifacts/jobs/job_1/parsed.json"),
        ],
    )

    indexer.index_completed_job(job, indexed_at=_now())

    resume = resume_repository.get("resume_job_1")
    profile = candidate_repository.get_profile("candidate_job_1")
    scores = candidate_repository.list_scores("candidate_job_1")
    findings = candidate_repository.list_findings("candidate_job_1")
    evidence = evidence_repository.list_by_candidate("candidate_job_1")

    assert resume is not None
    assert resume.parsed_document_id == "local://artifacts/jobs/job_1/parsed.json"
    assert profile is not None
    assert profile.source_document_artifact_uri == "local://artifacts/jobs/job_1/source.pdf"
    assert scores[0].total_score == 91
    assert findings[0].evidence_ids == ["evidence_finding_1_0"]
    assert evidence[0].parsed_document_artifact_uri == "local://artifacts/jobs/job_1/parsed.json"
    assert "parsed_document" not in EvidenceIndexRecord.model_fields


def test_review_result_indexer_ignores_non_completed_jobs() -> None:
    resume_repository = InMemoryResumeRepository()
    indexer = ReviewResultIndexer(
        resume_repository=resume_repository,
        candidate_repository=InMemoryCandidateRepository(),
        evidence_repository=InMemoryEvidenceRepository(),
    )
    job = AuditJob(job_id="job_1", file_path="ada.pdf", status=AuditJobStatus.failed)

    indexer.index_completed_job(job, indexed_at=_now())

    assert resume_repository.get("resume_job_1") is None


def _finding() -> AuditFinding:
    return AuditFinding(
        finding_id="finding_1",
        rule_id="rule_1",
        title="Risk",
        description="Risk description",
        risk_level=RiskLevel.medium,
        confidence=0.8,
        evidences=[
            Evidence(
                document_id="doc_1",
                page_number=1,
                block_id="block_1",
                quote="React TypeScript",
                bbox=BBox(x0=10, y0=20, x1=100, y1=40),
            )
        ],
        source_agent="extractor",
    )


def _score() -> ScoreResult:
    return ScoreResult(
        candidate_id="doc_1",
        template_id="frontend_engineer",
        template_version="v1",
        total_score=91,
        layer=CandidateLayer.best,
        dimension_scores={"ability_match": 90},
        advantage_tags=["React"],
        calculation_details=[],
        risk_count=1,
        created_at=_now(),
    )


def _artifact(artifact_type: str, artifact_uri: str) -> ArtifactRef:
    return ArtifactRef(
        artifact_uri=artifact_uri,
        artifact_type=artifact_type,
        content_type="application/json",
        sha256="a" * 64,
        size_bytes=128,
    )


def _now() -> datetime:
    return datetime(2026, 5, 20, tzinfo=timezone.utc)
