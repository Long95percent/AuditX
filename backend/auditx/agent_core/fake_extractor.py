from auditx.agent_core.extractor import FindingExtractor
from auditx.domain.audit import AuditFinding, Evidence, RiskLevel
from auditx.domain.documents import BBox, ParsedDocument


class FakeExtractor(FindingExtractor):
    def __init__(self, include_invalid_finding: bool = False) -> None:
        self.include_invalid_finding = include_invalid_finding

    def extract(self, document: ParsedDocument) -> list[AuditFinding]:
        valid_finding = AuditFinding(
            finding_id="fake_valid_finding",
            rule_id="hr.timeline.fake_risk",
            title="模拟时间线风险",
            description="用于验证审计闭环的模拟风险点。",
            risk_level=RiskLevel.medium,
            confidence=0.8,
            evidences=[
                Evidence(
                    document_id=document.document_id,
                    page_number=1,
                    block_id="p1_b1",
                    quote="任职于 A 公司",
                    bbox=BBox(x0=96, y0=180, x1=720, y1=224),
                )
            ],
            suggestion="请在真实规则接入后替换该模拟风险。",
            source_agent="fake_extractor",
        )
        findings = [valid_finding]
        if self.include_invalid_finding:
            findings.append(
                AuditFinding(
                    finding_id="fake_invalid_finding",
                    rule_id="hr.timeline.fake_risk",
                    title="无效模拟风险",
                    description="该风险引用不存在的 block，应被证据校验剔除。",
                    risk_level=RiskLevel.high,
                    confidence=0.95,
                    evidences=[
                        Evidence(
                            document_id=document.document_id,
                            page_number=1,
                            block_id="missing_block",
                            quote="不存在的证据",
                            bbox=BBox(x0=1, y0=1, x1=2, y1=2),
                        )
                    ],
                    suggestion="该 finding 不应进入最终结果。",
                    source_agent="fake_extractor",
                )
            )
        return findings
