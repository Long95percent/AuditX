from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class BatchStatus(StrEnum):
    draft = "draft"
    running = "running"
    completed = "completed"
    failed = "failed"


class BatchCandidateStatus(StrEnum):
    pending = "pending"
    reviewing = "reviewing"
    reviewed = "reviewed"
    shortlisted = "shortlisted"
    eliminated = "eliminated"
    failed = "failed"


class BatchRecord(BaseModel):
    batch_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    status: BatchStatus = BatchStatus.draft
    job_template_id: str = Field(min_length=1)
    run_config: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class BatchCandidate(BaseModel):
    batch_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    status: BatchCandidateStatus = BatchCandidateStatus.pending
    rank: int | None = Field(default=None, ge=1)
    score_id: str | None = None
    included_reason: str | None = None
    eliminated_reason: str | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
