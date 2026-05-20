from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from auditx.api.dependencies import get_resume_library_service
from auditx.application.resume_library_service import ResumeLibraryService
from auditx.domain.resume_library import ResumeRecord, ResumeStatus

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


class ImportResumeRequest(BaseModel):
    resume_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    parsed_document_artifact_uri: str | None = None
    imported_at: datetime


class ResumeListResponse(BaseModel):
    resumes: list[ResumeRecord]


@router.post("/import", response_model=ResumeRecord)
def import_resume(
    request: ImportResumeRequest,
    service: ResumeLibraryService = Depends(get_resume_library_service),
) -> ResumeRecord:
    return service.import_resume(
        resume_id=request.resume_id,
        filename=request.filename,
        parsed_document_artifact_uri=request.parsed_document_artifact_uri,
        imported_at=request.imported_at,
    )


@router.get("", response_model=ResumeListResponse)
def list_resumes(
    status: ResumeStatus | None = None,
    service: ResumeLibraryService = Depends(get_resume_library_service),
) -> ResumeListResponse:
    return ResumeListResponse(resumes=service.list_resumes(status=status))
