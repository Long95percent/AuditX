from abc import ABC, abstractmethod

from auditx.domain.audit import AuditFinding
from auditx.domain.documents import ParsedDocument


class FindingExtractor(ABC):
    @abstractmethod
    def extract(self, document: ParsedDocument) -> list[AuditFinding]:
        raise NotImplementedError
