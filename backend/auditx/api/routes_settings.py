from fastapi import APIRouter, Depends

from auditx.api.dependencies import get_openai_settings_service
from auditx.api.schemas import OpenAISettingsRequest, OpenAISettingsResponse
from auditx.application.openai_settings_service import OpenAISettingsService
from auditx.infrastructure.llm.job_template_provider import OpenAISettings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.post("/openai", response_model=OpenAISettingsResponse)
def update_openai_settings(
    request: OpenAISettingsRequest,
    service: OpenAISettingsService = Depends(get_openai_settings_service),
) -> OpenAISettingsResponse:
    settings = service.update(
        OpenAISettings(api_key=request.api_key, model=request.model, base_url=request.base_url)
    )
    return OpenAISettingsResponse(
        configured=service.configured(),
        model=settings.model,
        base_url=settings.base_url,
    )


@router.post("/openai/test", response_model=OpenAISettingsResponse)
def test_openai_settings(
    service: OpenAISettingsService = Depends(get_openai_settings_service),
) -> OpenAISettingsResponse:
    settings = service.get()
    return OpenAISettingsResponse(
        configured=service.configured(),
        model=settings.model,
        base_url=settings.base_url,
    )
