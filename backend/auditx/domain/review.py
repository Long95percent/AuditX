from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, Field

from auditx.domain.audit import AuditFinding, Evidence, RiskLevel


class ReviewStepStatus(StrEnum):
    started = "started"
    accepted = "accepted"
    rejected = "rejected"
    failed = "failed"


class ReviewTraceStep(BaseModel):
    step_id: str = Field(min_length=1)
    step_type: str = Field(min_length=1)
    name: str = Field(min_length=1)
    status: ReviewStepStatus
    input_summary: str = ""
    output_summary: str = ""
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewTrace(BaseModel):
    steps: list[ReviewTraceStep] = Field(default_factory=list)


class FindingCandidate(BaseModel):
    candidate_id: str = Field(min_length=1)
    rule_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    risk_level: RiskLevel
    confidence: Annotated[float, Field(ge=0, le=1)]
    evidences: list[Evidence] = Field(default_factory=list)
    suggestion: str = ""
    source_agent: str = Field(min_length=1)
    rejection_reason: str | None = None


class ReviewReportDraft(BaseModel):
    findings: list[AuditFinding] = Field(default_factory=list)
    rejected_count: int = Field(default=0, ge=0)
    candidates: list[FindingCandidate] = Field(default_factory=list)
    rejected_candidates: list[FindingCandidate] = Field(default_factory=list)
    trace: ReviewTrace = Field(default_factory=ReviewTrace)
