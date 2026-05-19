from auditx.domain.scoring import JobTemplate
from auditx.infrastructure.llm.job_template_provider import JobTemplateLLMProvider


class JobTemplateService:
    def __init__(self, provider: JobTemplateLLMProvider) -> None:
        self.provider = provider

    def create_from_jd(self, job_name: str, jd: str) -> JobTemplate:
        return self.provider.generate_from_jd(job_name=job_name, jd=jd)
