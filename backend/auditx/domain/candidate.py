from datetime import datetime

from pydantic import BaseModel, Field

from auditx.domain.scoring import CandidateLayer


class CandidateProfile(BaseModel):
    candidate_id: str = Field(min_length=1)
    resume_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    source_file_path: str | None = None
    source_document_artifact_uri: str | None = None
    review_session_id: str | None = None
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CandidateScoreRecord(BaseModel):
    score_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    review_session_id: str = Field(min_length=1)
    template_id: str = Field(min_length=1)
    template_version: str = Field(min_length=1)
    total_score: float = Field(ge=0, le=100)
    layer: CandidateLayer
    dimension_scores: dict[str, int] = Field(default_factory=dict)
    advantage_tags: list[str] = Field(default_factory=list)
    risk_count: int = Field(default=0, ge=0)
    batch_id: str | None = None
    created_at: datetime


class CandidateFindingRecord(BaseModel):
    finding_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    review_session_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    risk_level: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str] = Field(min_length=1)
    created_at: datetime
