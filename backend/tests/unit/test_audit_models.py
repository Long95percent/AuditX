import pytest
from pydantic import ValidationError

from auditx.domain.audit import AuditFinding, Evidence, RiskLevel
from auditx.domain.documents import BBox


def test_audit_finding_requires_at_least_one_evidence() -> None:
    with pytest.raises(ValidationError):
        AuditFinding(
            finding_id="finding_1",
            rule_id="rule_1",
            title="Risk",
            description="Risk description",
            risk_level=RiskLevel.high,
            confidence=0.9,
            evidences=[],
            source_agent="extractor",
        )


def test_evidence_requires_valid_bbox() -> None:
    with pytest.raises(ValidationError):
        Evidence(
            document_id="doc_1",
            page_number=1,
            block_id="block_1",
            quote="sample",
            bbox=BBox(x0=10, y0=10, x1=5, y1=20),
        )
