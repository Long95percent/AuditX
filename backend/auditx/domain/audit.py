from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

from auditx.domain.documents import BBox


class RiskLevel(StrEnum):
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class Evidence(BaseModel):
    document_id: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    block_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    bbox: BBox
    start_offset: int | None = Field(default=None, ge=0)
    end_offset: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def offsets_must_be_ordered(self) -> "Evidence":
        if self.start_offset is not None and self.end_offset is not None:
            if self.end_offset <= self.start_offset:
                raise ValueError("end_offset must be greater than start_offset")
        return self


class AuditFinding(BaseModel):
    finding_id: str = Field(min_length=1)
    rule_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    risk_level: RiskLevel
    confidence: Annotated[float, Field(ge=0, le=1)]
    evidences: list[Evidence] = Field(min_length=1)
    suggestion: str = ""
    source_agent: str = Field(min_length=1)
