from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from auditx.api.dependencies import get_audit_job_service
from auditx.api.schemas import AuditFindingsResponse, AuditJobResponse, CreateAuditJobRequest
from auditx.application.audit_job_service import AuditJobService
from auditx.config.settings import Settings, get_settings

router = APIRouter(prefix="/api/audit-jobs", tags=["audit-jobs"])


@router.post("", response_model=AuditJobResponse)
def create_audit_job(
    request: CreateAuditJobRequest,
    background_tasks: BackgroundTasks,
    service: AuditJobService = Depends(get_audit_job_service),
    settings: Settings = Depends(get_settings),
) -> AuditJobResponse:
    document_path = Path(request.file_path)
    if not document_path.exists():
        raise HTTPException(status_code=400, detail="Selected document does not exist")
    if not document_path.is_file():
        raise HTTPException(status_code=400, detail="Selected document is not a file")
    resolved_path = document_path.resolve()
    if not _is_path_allowed(resolved_path, settings.allowed_document_roots):
        raise HTTPException(
            status_code=400,
            detail="Selected document is outside allowed document roots",
        )
    job = service.create(str(resolved_path))
    background_tasks.add_task(service.run, job.job_id)
    return AuditJobResponse.model_validate(job)


def _is_path_allowed(document_path: Path, allowed_roots: list[str]) -> bool:
    for root in allowed_roots:
        try:
            document_path.relative_to(Path(root).expanduser().resolve())
            return True
        except ValueError:
            continue
    return False


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