import pytest

from auditx.application.job_template_service import JobTemplateService
from auditx.infrastructure.llm.job_template_provider import (
    FakeJobTemplateLLMProvider,
    MissingOpenAIAPIKeyError,
    OpenAIJobTemplateProvider,
    OpenAISettings,
)


def test_openai_provider_requires_api_key_and_does_not_fallback_to_rules() -> None:
    provider = OpenAIJobTemplateProvider(settings=OpenAISettings(api_key="", model="gpt-5.4-mini"))

    with pytest.raises(MissingOpenAIAPIKeyError):
        provider.generate_from_jd(job_name="增长产品经理", jd="负责增长策略和用户研究")


def test_fake_llm_provider_generates_valid_job_template_for_tests_only() -> None:
    provider = FakeJobTemplateLLMProvider()

    template = provider.generate_from_jd(job_name="增长产品经理", jd="负责增长策略和用户研究")

    assert template.name == "增长产品经理"
    assert template.template_id == "custom_growth_product_manager"
    assert template.hard_requirements
    assert template.advantage_dictionary
    assert template.risk_strategy
    assert template.version == "v1"


def test_job_template_service_uses_llm_provider_output() -> None:
    service = JobTemplateService(provider=FakeJobTemplateLLMProvider())

    template = service.create_from_jd(job_name="增长产品经理", jd="负责增长策略和用户研究")

    assert template.template_id == "custom_growth_product_manager"
