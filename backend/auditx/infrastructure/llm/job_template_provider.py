from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from auditx.domain.scoring import JobTemplate


class MissingOpenAIAPIKeyError(RuntimeError):
    pass


class OpenAISettings(BaseModel):
    api_key: str | None = None
    model: str = "gpt-5.4-mini"
    base_url: str = "https://api.openai.com/v1"


class JobTemplateLLMProvider(ABC):
    @abstractmethod
    def generate_from_jd(self, job_name: str, jd: str) -> JobTemplate:
        raise NotImplementedError


class OpenAIJobTemplateProvider(JobTemplateLLMProvider):
    def __init__(self, settings: OpenAISettings) -> None:
        self.settings = settings

    def generate_from_jd(self, job_name: str, jd: str) -> JobTemplate:
        if not self.settings.api_key:
            raise MissingOpenAIAPIKeyError("OpenAI API key is not configured")
        raise NotImplementedError("OpenAI Responses API call is not implemented in this offline skeleton")

    def build_responses_payload(self, job_name: str, jd: str) -> dict[str, Any]:
        return {
            "model": self.settings.model,
            "input": [
                {
                    "role": "system",
                    "content": "Generate an AuditX JobTemplate from the user's job name and JD.",
                },
                {"role": "user", "content": f"Job name: {job_name}\nJD:\n{jd}"},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "auditx_job_template",
                    "schema": self.job_template_json_schema(),
                    "strict": True,
                }
            },
        }

    def job_template_json_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "template_id",
                "name",
                "version",
                "hard_requirements",
                "weights",
                "advantage_dictionary",
                "risk_strategy",
            ],
            "properties": {
                "template_id": {"type": "string"},
                "name": {"type": "string"},
                "version": {"type": "string"},
                "hard_requirements": {"type": "array", "items": {"type": "string"}},
                "weights": {"type": "object", "additionalProperties": {"type": "number"}},
                "advantage_dictionary": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
                "risk_strategy": {"type": "object", "additionalProperties": {"type": "string"}},
            },
        }


class FakeJobTemplateLLMProvider(JobTemplateLLMProvider):
    def generate_from_jd(self, job_name: str, jd: str) -> JobTemplate:
        return JobTemplate(
            template_id="custom_growth_product_manager",
            name=job_name,
            version="v1",
            hard_requirements=["理解岗位 JD", "能基于业务目标拆解要求"],
            weights={
                "completeness": 0.1,
                "hard_requirement_match": 0.3,
                "ability_match": 0.25,
                "experience_relevance": 0.25,
                "advantage_bonus": 0.1,
            },
            advantage_dictionary={"growth": "增长策略", "user_research": "用户研究"},
            risk_strategy={"missing_contact": "low", "unclear_jd_match": "medium"},
        )
