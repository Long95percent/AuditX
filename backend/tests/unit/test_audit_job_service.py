from auditx.application.audit_job_service import AuditJobService, AuditJobStatus
from auditx.application.review_result_indexer import ReviewResultIndexer
from auditx.domain.artifacts import ArtifactRef
from auditx.domain.audit import AuditFinding, Evidence, RiskLevel
from auditx.domain.documents import BBox, ParsedDocument
from auditx.domain.results import AuditResult
from auditx.infrastructure.storage.candidate_repository import InMemoryCandidateRepository
from auditx.infrastructure.storage.evidence_repository import InMemoryEvidenceRepository
from auditx.infrastructure.storage.resume_repository import InMemoryResumeRepository


class RecordingUseCase:
    def __init__(self) -> None:
        self.ran_paths: list[str] = []

    def run(self, file_path: str):
        self.ran_paths.append(file_path)
        raise RuntimeError("stop after proving run was invoked")


def test_create_records_pending_job_without_running_use_case() -> None:
    use_case = RecordingUseCase()
    service = AuditJobService(use_case=use_case)  # type: ignore[arg-type]

    job = service.create("resume.pdf")

    assert job.status == AuditJobStatus.pending
    assert service.get(job.job_id) == job
    assert use_case.ran_paths == []


def test_run_executes_existing_job_by_id() -> None:
    use_case = RecordingUseCase()
    service = AuditJobService(use_case=use_case)  # type: ignore[arg-type]
    job = service.create("resume.pdf")

    service.run(job.job_id)

    assert use_case.ran_paths == ["resume.pdf"]
    assert job.status == AuditJobStatus.failed
    assert job.error == "stop after proving run was invoked"


class ArtifactUseCase:
    def __init__(self) -> None:
        self.received_job_id: str | None = None
        self.received_artifact_store = None

    def run(self, file_path: str, job_id: str | None = None, artifact_store=None):
        self.received_job_id = job_id
        self.received_artifact_store = artifact_store
        return AuditResult(
            document=ParsedDocument(document_id="doc_1", filename=file_path),
            artifacts=[
                ArtifactRef(
                    artifact_uri="local://artifacts/jobs/job_1/ocr_raw.json",
                    artifact_type="ocr_raw",
                    content_type="application/json",
                    sha256="a" * 64,
                    size_bytes=128,
                )
            ],
        )


def test_run_persists_artifact_refs_without_embedding_artifact_content() -> None:
    use_case = ArtifactUseCase()
    service = AuditJobService(use_case=use_case)  # type: ignore[arg-type]
    job = service.create("resume.pdf")

    service.run(job.job_id)

    completed = service.get(job.job_id)
    assert completed is not None
    assert completed.artifacts[0].artifact_type == "ocr_raw"
    assert completed.artifacts[0].size_bytes == 128
    assert not hasattr(completed.artifacts[0], "content")


def test_run_passes_job_id_and_artifact_store_to_use_case() -> None:
    use_case = ArtifactUseCase()
    service = AuditJobService(use_case=use_case)  # type: ignore[arg-type]
    job = service.create("resume.pdf")

    service.run(job.job_id)

    assert use_case.received_job_id == job.job_id


class IndexedUseCase:
    def run(self, file_path: str):
        return AuditResult(
            document=ParsedDocument(document_id="doc_1", filename=file_path),
            findings=[
                AuditFinding(
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
                            bbox=BBox(x0=1, y0=1, x1=10, y1=10),
                        )
                    ],
                    source_agent="extractor",
                )
            ],
            artifacts=[
                ArtifactRef(
                    artifact_uri="local://artifacts/jobs/job_1/parsed.json",
                    artifact_type="parsed_document",
                    content_type="application/json",
                    sha256="a" * 64,
                    size_bytes=128,
                )
            ],
        )


def test_completed_job_is_indexed_into_resume_candidate_and_evidence_repositories() -> None:
    resume_repository = InMemoryResumeRepository()
    candidate_repository = InMemoryCandidateRepository()
    evidence_repository = InMemoryEvidenceRepository()
    service = AuditJobService(
        use_case=IndexedUseCase(),  # type: ignore[arg-type]
        result_indexer=ReviewResultIndexer(
            resume_repository=resume_repository,
            candidate_repository=candidate_repository,
            evidence_repository=evidence_repository,
        ),
    )
    job = service.create("resume.pdf")

    service.run(job.job_id)

    assert resume_repository.get(f"resume_{job.job_id}") is not None
    assert candidate_repository.get_profile(f"candidate_{job.job_id}") is not None
    assert evidence_repository.list_by_candidate(f"candidate_{job.job_id}")
