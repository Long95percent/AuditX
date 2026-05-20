from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ArtifactRef(BaseModel):
    artifact_uri: str = Field(min_length=1)
    artifact_type: str = Field(min_length=1)
    content_type: str = Field(default="application/octet-stream", min_length=1)
    sha256: str = Field(min_length=1)
    size_bytes: int = Field(ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
