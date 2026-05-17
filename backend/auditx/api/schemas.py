from pydantic import BaseModel, ConfigDict, Field

from auditx.application.audit_job_service import AuditJobStatus
from auditx.domain.audit import AuditFinding


class CreateAuditJobRequest(BaseModel):
    file_path: str = Field(min_length=1)


class AuditJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    file_path: str
    status: AuditJobStatus
    document_id: str | None = None
    findings: list[AuditFinding] = Field(default_factory=list)
    rejected_count: int = 0
    error: str | None = None


class AuditFindingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    findings: list[AuditFinding] = Field(default_factory=list)
