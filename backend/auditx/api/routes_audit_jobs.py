from pathlib import Path
import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from auditx.api.dependencies import get_audit_job_service
from auditx.api.schemas import AuditFindingsResponse, AuditJobResponse, CreateAuditJobRequest
from auditx.application.audit_job_service import AuditJobService
from auditx.config.settings import Settings, get_settings
from auditx.infrastructure.storage.artifact_store import FileSystemArtifactStore

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


@router.get("/{job_id}/findings", response_model=AuditFindingsResponse)
def get_audit_job_findings(
    job_id: str,
    service: AuditJobService = Depends(get_audit_job_service),
) -> AuditFindingsResponse:
    findings = service.findings(job_id)
    if findings is None:
        raise HTTPException(status_code=404, detail="Audit job not found")
    return AuditFindingsResponse(job_id=job_id, findings=findings)


@router.get("/{job_id}/document")
def get_audit_job_document(
    job_id: str,
    service: AuditJobService = Depends(get_audit_job_service),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    job = service.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Audit job not found")
    source_artifact = next(
        (artifact for artifact in job.artifacts if artifact.artifact_type == "source_document"),
        None,
    )
    if source_artifact is None:
        raise HTTPException(status_code=404, detail="Source document artifact not found")
    store = FileSystemArtifactStore(Path(settings.storage_dir) / "artifacts")
    path = store.resolve(source_artifact)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Source document artifact file not found")
    return FileResponse(path, media_type=source_artifact.content_type, filename=Path(job.file_path).name)


@router.get("/{job_id}/parsed-document")
def get_audit_job_parsed_document(
    job_id: str,
    service: AuditJobService = Depends(get_audit_job_service),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    job = service.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Audit job not found")
    parsed_artifact = next(
        (artifact for artifact in job.artifacts if artifact.artifact_type == "parsed_document"),
        None,
    )
    if parsed_artifact is None:
        raise HTTPException(status_code=404, detail="Parsed document artifact not found")
    if parsed_artifact.content_type != "application/json":
        raise HTTPException(status_code=415, detail="Parsed document artifact is not JSON")
    store = FileSystemArtifactStore(Path(settings.storage_dir) / "artifacts")
    path = store.resolve(parsed_artifact)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Parsed document artifact file not found")
    return JSONResponse(json.loads(path.read_text(encoding="utf-8")))


@router.get("/{job_id}", response_model=AuditJobResponse)
def get_audit_job(
    job_id: str,
    service: AuditJobService = Depends(get_audit_job_service),
) -> AuditJobResponse:
    job = service.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Audit job not found")
    return AuditJobResponse.model_validate(job)
