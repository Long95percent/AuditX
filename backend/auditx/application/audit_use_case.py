from auditx.agent_core.evidence_validator import EvidenceValidator
from auditx.agent_core.extractor import FindingExtractor
from auditx.agent_core.finding_normalizer import FindingNormalizer
from auditx.document_pipeline.base import DocumentParser
from auditx.domain.results import AuditResult


class AuditUseCase:
    def __init__(
        self,
        parser: DocumentParser,
        extractor: FindingExtractor,
        normalizer: FindingNormalizer,
        evidence_validator: EvidenceValidator | None = None,
    ) -> None:
        self.parser = parser
        self.extractor = extractor
        self.normalizer = normalizer
        self.evidence_validator = evidence_validator or EvidenceValidator()

    def run(self, file_path: str) -> AuditResult:
        document = self.parser.parse(file_path)
        candidate_findings = self.extractor.extract(document)
        accepted_findings = [
            finding
            for finding in candidate_findings
            if self.evidence_validator.validate(finding, document)
        ]
        return AuditResult(
            document=document,
            findings=self.normalizer.normalize(accepted_findings),
            rejected_count=len(candidate_findings) - len(accepted_findings),
        )
