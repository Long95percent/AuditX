from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from auditx.api.dependencies import get_audit_job_service
from auditx.api.schemas import AuditFindingsResponse, AuditJobResponse, CreateAuditJobRequest
from auditx.application.audit_job_service import AuditJobService

router = APIRouter(prefix="/api/audit-jobs", tags=["audit-jobs"])


@router.post("", response_model=AuditJobResponse)
def create_audit_job(
    request: CreateAuditJobRequest,
    service: AuditJobService = Depends(get_audit_job_service),
) -> AuditJobResponse:
    document_path = Path(request.file_path)
    if not document_path.exists():
        raise HTTPException(status_code=400, detail="Selected document does not exist")
    if not document_path.is_file():
        raise HTTPException(status_code=400, detail="Selected document is not a file")
    return AuditJobResponse.model_validate(service.create_and_run(request.file_path))


@router.get("/{job_id}", response_model=AuditJobResponse)
def get_audit_job(
    job_id: str,
    service: AuditJobService = Depends(get_audit_job_service),
) -> AuditJobResponse:
    job = service.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Audit job not found")
    return AuditJobResponse.model_validate(job)


@router.get("/{job_id}/findings", response_model=AuditFindingsResponse)
def get_audit_job_findings(
    job_id: str,
    service: AuditJobService = Depends(get_audit_job_service),
) -> AuditFindingsResponse:
    findings = service.findings(job_id)
    if findings is None:
        raise HTTPException(status_code=404, detail="Audit job not found")
    return AuditFindingsResponse(job_id=job_id, findings=findings)

