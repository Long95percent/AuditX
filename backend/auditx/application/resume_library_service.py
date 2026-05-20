from datetime import datetime

from auditx.domain.resume_library import ResumeRecord, ResumeStatus
from auditx.infrastructure.storage.resume_repository import InMemoryResumeRepository


class ResumeLibraryService:
    def __init__(self, repository: InMemoryResumeRepository) -> None:
        self.repository = repository

    def import_resume(
        self,
        resume_id: str,
        filename: str,
        parsed_document_artifact_uri: str | None,
        imported_at: datetime,
    ) -> ResumeRecord:
        resume = ResumeRecord(
            resume_id=resume_id,
            filename=filename,
            imported_at=imported_at,
            status=ResumeStatus.new,
            parsed_document_id=parsed_document_artifact_uri,
        )
        self.repository.save(resume)
        return resume

    def get_resume(self, resume_id: str) -> ResumeRecord | None:
        return self.repository.get(resume_id)

    def list_resumes(self, status: ResumeStatus | None = None) -> list[ResumeRecord]:
        return self.repository.list(status=status)
