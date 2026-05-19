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
    assert result.trace.steps[0].step_type == "agent"
    assert result.trace.steps[0].name == "fake_extractor.extract"


def test_audit_use_case_rejects_findings_without_matching_document_evidence() -> None:
    use_case = AuditUseCase(
        parser=FakeDocumentParser(),
        extractor=FakeExtractor(include_invalid_finding=True),
        normalizer=FindingNormalizer(),
    )

    result = use_case.run(file_path="demo_resume.pdf")

    assert len(result.findings) == 1
    assert all(finding.finding_id != "fake_invalid_finding" for finding in result.findings)
    assert result.rejected_count == 1
    assert any(step.status == "rejected" for step in result.trace.steps)


def test_audit_use_case_routes_extraction_through_registered_tool() -> None:
    from auditx.agent_core.extractor_tool import ExtractorTool
    from auditx.tool_registry.registry import ToolRegistry

    registry = ToolRegistry()
    registry.register(ExtractorTool(extractor=FakeExtractor()))
    use_case = AuditUseCase(
        parser=FakeDocumentParser(),
        extractor=FakeExtractor(include_invalid_finding=True),
        normalizer=FindingNormalizer(),
        tool_registry=registry,
    )

    result = use_case.run(file_path="demo_resume.pdf")

    assert len(result.findings) == 1
    assert result.rejected_count == 0
    assert result.trace.steps[0].step_type == "tool"
    assert result.trace.steps[0].metadata["tool_name"] == "agent.extractor.fake"
