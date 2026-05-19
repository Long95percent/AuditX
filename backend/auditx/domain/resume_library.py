from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from auditx.domain.scoring import JobTemplate


class ResumeStatus(StrEnum):
    new = "new"
    reviewed = "reviewed"
    shortlisted = "shortlisted"


class ResumeRecord(BaseModel):
    resume_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    imported_at: datetime
    status: ResumeStatus = ResumeStatus.new
    parsed_document_id: str | None = None


class RunConfig(BaseModel):
    top_n: int = Field(default=20, gt=0)


class ReviewContext(BaseModel):
    job_template: JobTemplate
    run_config: RunConfig = Field(default_factory=RunConfig)
    historical_context: dict[str, Any] = Field(default_factory=dict)
    reuse_parsed_result: bool = False
