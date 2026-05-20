from auditx.agent_core.evidence_validator import EvidenceValidator
from auditx.domain.audit import AuditFinding, Evidence, RiskLevel
from auditx.domain.documents import BBox, BlockType, DocumentPage, LayoutBlock, ParsedDocument


def test_evidence_validator_accepts_quote_bound_to_existing_block() -> None:
    bbox = BBox(x0=0, y0=0, x1=100, y1=40)
    document = ParsedDocument(
        document_id="doc_1",
        filename="resume.pdf",
        pages=[
            DocumentPage(
                page_number=1,
                width=800,
                height=1000,
                blocks=[
                    LayoutBlock(
                        block_id="p1_b1",
                        page_number=1,
                        block_type=BlockType.paragraph,
                        text="2022.03 - 2024.05 任职于 A 公司",
                        bbox=bbox,
                    )
                ],
            )
        ],
    )
    finding = AuditFinding(
        finding_id="finding_1",
        rule_id="hr.timeline.overlap",
        title="时间线风险",
        description="检测到疑似时间线冲突",
        risk_level=RiskLevel.high,
        confidence=0.92,
        evidences=[
            Evidence(
                document_id="doc_1",
                page_number=1,
                block_id="p1_b1",
                quote="任职于 A 公司",
                bbox=bbox,
            )
        ],
        source_agent="extractor",
    )

    assert EvidenceValidator().validate(finding, document) is True


def test_evidence_validator_rejects_finding_without_evidence() -> None:
    document = ParsedDocument(
        document_id="doc_1",
        filename="resume.pdf",
        pages=[
            DocumentPage(
                page_number=1,
                width=800,
                height=1000,
                blocks=[],
            )
        ],
    )
    finding = AuditFinding.model_construct(
        finding_id="finding_without_evidence",
        rule_id="llm.unverified",
        title="无证据风险",
        description="没有原文证据的风险不能进入正式 findings。",
        risk_level=RiskLevel.medium,
        confidence=0.5,
        evidences=[],
        source_agent="llm_mock",
    )

    assert EvidenceValidator().validate(finding, document) is False
