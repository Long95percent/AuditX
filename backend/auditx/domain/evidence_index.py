from datetime import datetime

from pydantic import BaseModel, Field


class EvidenceIndexRecord(BaseModel):
    evidence_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    resume_id: str = Field(min_length=1)
    parsed_document_artifact_uri: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    block_id: str = Field(min_length=1)
    text_excerpt: str = Field(min_length=1)
    bbox: dict[str, float] | None = None
    created_at: datetime
