from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

from auditx.application.audit_use_case import AuditUseCase
from auditx.domain.audit import AuditFinding
from auditx.domain.results import AuditResult


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
    error: str | None = None


class AuditJobService:
    def __init__(self, use_case: AuditUseCase) -> None:
        self.use_case = use_case
        self._jobs: dict[str, AuditJob] = {}

    def create_and_run(self, file_path: str) -> AuditJob:
        job = AuditJob(job_id=str(uuid4()), file_path=file_path, status=AuditJobStatus.pending)
        self._jobs[job.job_id] = job
        job.status = AuditJobStatus.running
        try:
            result = self.use_case.run(file_path=file_path)
            self._apply_result(job, result)
        except Exception as exc:
            job.status = AuditJobStatus.failed
            job.error = str(exc)
        return job

    def get(self, job_id: str) -> AuditJob | None:
        return self._jobs.get(job_id)

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
