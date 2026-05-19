from auditx.infrastructure.llm.job_template_provider import OpenAISettings


class OpenAISettingsService:
    def __init__(self) -> None:
        self._settings = OpenAISettings()

    def update(self, settings: OpenAISettings) -> OpenAISettings:
        self._settings = settings
        return self._settings

    def get(self) -> OpenAISettings:
        return self._settings

    def configured(self) -> bool:
        return bool(self._settings.api_key)
