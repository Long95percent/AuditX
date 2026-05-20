from pydantic import BaseModel, Field

from auditx.domain.audit import AuditFinding
from auditx.domain.artifacts import ArtifactRef
from auditx.domain.documents import ParsedDocument
from auditx.domain.review import FindingCandidate, ReviewTrace
from auditx.domain.scoring import ScoreResult


class AuditResult(BaseModel):
    document: ParsedDocument
    findings: list[AuditFinding] = Field(default_factory=list)
    rejected_count: int = 0
    candidates: list[FindingCandidate] = Field(default_factory=list)
    rejected_candidates: list[FindingCandidate] = Field(default_factory=list)
    score: ScoreResult | None = None
    trace: ReviewTrace = Field(default_factory=ReviewTrace)
    artifacts: list[ArtifactRef] = Field(default_factory=list)
