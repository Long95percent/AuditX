from auditx.domain.audit import AuditFinding
from auditx.domain.documents import ParsedDocument


class EvidenceValidator:
    def validate(self, finding: AuditFinding, document: ParsedDocument) -> bool:
        if not finding.evidences:
            return False
        blocks_by_id = {
            block.block_id: block
            for page in document.pages
            for block in page.blocks
        }
        for evidence in finding.evidences:
            block = blocks_by_id.get(evidence.block_id)
            if block is None:
                return False
            if block.page_number != evidence.page_number:
                return False
            if evidence.quote not in block.text:
                return False
        return True
