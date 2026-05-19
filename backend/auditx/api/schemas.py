from pydantic import BaseModel, ConfigDict, Field

from auditx.application.audit_job_service import AuditJobStatus
from auditx.domain.audit import AuditFinding
from auditx.domain.review import FindingCandidate, ReviewTrace
from auditx.domain.scoring import ScoreResult


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
    candidates: list[FindingCandidate] = Field(default_factory=list)
    rejected_candidates: list[FindingCandidate] = Field(default_factory=list)
    score: ScoreResult | None = None
    trace: ReviewTrace = Field(default_factory=ReviewTrace)
    error: str | None = None


class AuditFindingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    findings: list[AuditFinding] = Field(default_factory=list)


class OpenAISettingsRequest(BaseModel):
    api_key: str | None = None
    model: str = "gpt-5.4-mini"
    base_url: str = "https://api.openai.com/v1"


class OpenAISettingsResponse(BaseModel):
    configured: bool
    api_key: None = None
    model: str
    base_url: str


class CreateJobTemplateFromJDRequest(BaseModel):
    job_name: str = Field(min_length=1)
    jd: str = Field(min_length=1)
