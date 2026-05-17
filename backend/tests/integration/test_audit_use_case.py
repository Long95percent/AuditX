from auditx.agent_core.fake_extractor import FakeExtractor
from auditx.agent_core.finding_normalizer import FindingNormalizer
from auditx.application.audit_use_case import AuditUseCase
from auditx.document_pipeline.fake_parser import FakeDocumentParser


def test_audit_use_case_returns_only_evidence_backed_findings() -> None:
    use_case = AuditUseCase(
        parser=FakeDocumentParser(),
        extractor=FakeExtractor(),
        normalizer=FindingNormalizer(),
    )

    result = use_case.run(file_path="demo_resume.pdf")

    assert result.document.document_id == "fake_doc_001"
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.rule_id == "hr.timeline.fake_risk"
    assert finding.evidences[0].block_id == "p1_b1"
    assert finding.evidences[0].bbox.x1 > finding.evidences[0].bbox.x0


def test_audit_use_case_rejects_findings_without_matching_document_evidence() -> None:
    use_case = AuditUseCase(
        parser=FakeDocumentParser(),
        extractor=FakeExtractor(include_invalid_finding=True),
        normalizer=FindingNormalizer(),
    )

    result = use_case.run(file_path="demo_resume.pdf")

    assert len(result.findings) == 1
    assert all(finding.finding_id != "fake_invalid_finding" for finding in result.findings)
