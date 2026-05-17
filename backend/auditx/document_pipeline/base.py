from abc import ABC, abstractmethod

from auditx.domain.documents import ParsedDocument


class DocumentParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        raise NotImplementedError
