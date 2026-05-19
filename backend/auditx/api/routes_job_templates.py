from fastapi import APIRouter, Depends, HTTPException

from auditx.api.dependencies import get_openai_settings_service
from auditx.api.schemas import CreateJobTemplateFromJDRequest
from auditx.application.job_template_service import JobTemplateService
from auditx.application.openai_settings_service import OpenAISettingsService
from auditx.domain.scoring import JobTemplate
from auditx.infrastructure.llm.job_template_provider import (
    MissingOpenAIAPIKeyError,
    OpenAIJobTemplateProvider,
)

router = APIRouter(prefix="/api/job-templates", tags=["job-templates"])


@router.post("/from-jd", response_model=JobTemplate)
def create_job_template_from_jd(
    request: CreateJobTemplateFromJDRequest,
    settings_service: OpenAISettingsService = Depends(get_openai_settings_service),
) -> JobTemplate:
    service = JobTemplateService(provider=OpenAIJobTemplateProvider(settings_service.get()))
    try:
        return service.create_from_jd(job_name=request.job_name, jd=request.jd)
    except MissingOpenAIAPIKeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
