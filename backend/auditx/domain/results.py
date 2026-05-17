from pydantic import BaseModel, Field

from auditx.domain.audit import AuditFinding
from auditx.domain.documents import ParsedDocument


class AuditResult(BaseModel):
    document: ParsedDocument
    findings: list[AuditFinding] = Field(default_factory=list)
    rejected_count: int = 0
