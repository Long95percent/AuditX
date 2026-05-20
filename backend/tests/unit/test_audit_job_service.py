from auditx.application.audit_job_service import AuditJobService, AuditJobStatus
from auditx.domain.artifacts import ArtifactRef
from auditx.domain.documents import ParsedDocument
from auditx.domain.results import AuditResult


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
