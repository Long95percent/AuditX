from enum import StrEnum
import inspect
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, Field

from auditx.application.audit_use_case import AuditUseCase
from auditx.domain.audit import AuditFinding
from auditx.domain.artifacts import ArtifactRef
from auditx.domain.review import FindingCandidate, ReviewTrace
from auditx.domain.results import AuditResult
from auditx.domain.scoring import ScoreResult
from auditx.infrastructure.storage.artifact_store import FileSystemArtifactStore


class AuditJobStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class AuditJob(BaseModel):
    job_id: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    status: AuditJobStatus
    document_id: str | None = None
    findings: list[AuditFinding] = Field(default_factory=list)
    rejected_count: int = 0
    candidates: list[FindingCandidate] = Field(default_factory=list)
    rejected_candidates: list[FindingCandidate] = Field(default_factory=list)
    score: ScoreResult | None = None
    trace: ReviewTrace = Field(default_factory=ReviewTrace)
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    error: str | None = None


class AuditJobRepository(Protocol):
    def save(self, job: AuditJob) -> None:
        pass

    def get(self, job_id: str) -> AuditJob | None:
        pass


class InMemoryAuditJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[str, AuditJob] = {}

    def save(self, job: AuditJob) -> None:
        self._jobs[job.job_id] = job

    def get(self, job_id: str) -> AuditJob | None:
        return self._jobs.get(job_id)


class AuditJobService:
    def __init__(
        self,
        use_case: AuditUseCase,
        repository: AuditJobRepository | None = None,
        artifact_store: FileSystemArtifactStore | None = None,
    ) -> None:
        self.use_case = use_case
        self.repository = repository or InMemoryAuditJobRepository()
        self.artifact_store = artifact_store

    def create(self, file_path: str) -> AuditJob:
        job = AuditJob(job_id=str(uuid4()), file_path=file_path, status=AuditJobStatus.pending)
        self.repository.save(job)
        return job

    def create_and_run(self, file_path: str) -> AuditJob:
        job = self.create(file_path)
        self.run(job.job_id)
        return self.get(job.job_id) or job

    def run(self, job_id: str) -> None:
        job = self.repository.get(job_id)
        if job is None:
            return
        job.status = AuditJobStatus.running
        self.repository.save(job)
        try:
            self._capture_source_document(job)
            result = self._run_use_case(job)
            self._apply_result(job, result)
        except Exception as exc:
            job.status = AuditJobStatus.failed
            job.error = str(exc)
        self.repository.save(job)

    def get(self, job_id: str) -> AuditJob | None:
        return self.repository.get(job_id)

    def findings(self, job_id: str) -> list[AuditFinding] | None:
        job = self.get(job_id)
        if job is None:
            return None
        return job.findings

    def _apply_result(self, job: AuditJob, result: AuditResult) -> None:
        job.status = AuditJobStatus.completed
        job.document_id = result.document.document_id
        job.findings = result.findings
        job.rejected_count = result.rejected_count
        job.candidates = result.candidates
        job.rejected_candidates = result.rejected_candidates
        job.score = result.score
        job.trace = result.trace
        job.artifacts.extend(result.artifacts)

    def _run_use_case(self, job: AuditJob) -> AuditResult:
        parameters = inspect.signature(self.use_case.run).parameters
        if "job_id" in parameters or "artifact_store" in parameters:
            return self.use_case.run(
                file_path=job.file_path,
                job_id=job.job_id,
                artifact_store=self.artifact_store,
            )
        return self.use_case.run(file_path=job.file_path)

    def _capture_source_document(self, job: AuditJob) -> None:
        if self.artifact_store is None:
            return
        path = Path(job.file_path)
        if not path.is_file():
            return
        artifact = self.artifact_store.write_bytes(
            owner_type="job",
            owner_id=job.job_id,
            artifact_type="source_document",
            filename=path.name,
            content=path.read_bytes(),
            content_type="application/pdf" if path.suffix.lower() == ".pdf" else "application/octet-stream",
        )
        job.artifacts.append(artifact)
        self.repository.save(job)
