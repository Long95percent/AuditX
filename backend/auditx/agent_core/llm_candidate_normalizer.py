from auditx.agent_core.llm_mock_provider import LLMMockOutput
from auditx.domain.audit import Evidence
from auditx.domain.documents import ParsedDocument
from auditx.domain.review import FindingCandidate


class LLMCandidateNormalizer:
    def normalize(self, output: LLMMockOutput, document: ParsedDocument) -> list[FindingCandidate]:
        return [
            FindingCandidate(
                candidate_id=candidate.candidate_id,
                rule_id=candidate.rule_id,
                title=candidate.title,
                description=candidate.description,
                risk_level=candidate.risk_level,
                confidence=candidate.confidence,
                evidences=self._find_evidences(candidate.evidence_quote, document),
                suggestion=candidate.suggestion,
                source_agent="llm_mock",
            )
            for candidate in output.candidates
        ]

    def _find_evidences(self, quote: str | None, document: ParsedDocument) -> list[Evidence]:
        if not quote:
            return []
        for page in document.pages:
            for block in page.blocks:
                if quote in block.text:
                    return [
                        Evidence(
                            document_id=document.document_id,
                            page_number=block.page_number,
                            block_id=block.block_id,
                            quote=quote,
                            bbox=block.bbox,
                        )
                    ]
        return []
