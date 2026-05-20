from functools import lru_cache
from pathlib import Path

from auditx.agent_core.extractor_tool import ExtractorTool
from auditx.agent_core.fake_extractor import FakeExtractor
from auditx.agent_core.finding_normalizer import FindingNormalizer
from auditx.agent_core.llm_candidate_tool import LLMCandidateTool
from auditx.agent_core.rule_tools import (
    AdvantageDictionaryTool,
    ContactMissingRuleTool,
    EducationMissingRuleTool,
    KeywordMatchRuleTool,
    YearsExperienceRuleTool,
)
from auditx.application.audit_job_service import AuditJobService
from auditx.application.audit_use_case import AuditUseCase
from auditx.application.openai_settings_service import OpenAISettingsService
from auditx.config.settings import get_settings
from auditx.document_pipeline.fake_parser import FakeDocumentParser
from auditx.domain.scoring import JobTemplate
from auditx.infrastructure.storage.audit_job_repository import SQLiteAuditJobRepository
from auditx.tool_registry.registry import ToolRegistry


@lru_cache(maxsize=1)
def get_openai_settings_service() -> OpenAISettingsService:
    return OpenAISettingsService()


@lru_cache(maxsize=1)
def get_audit_job_service() -> AuditJobService:
    settings = get_settings()
    extractor = FakeExtractor()
    tool_registry = ToolRegistry()
    tool_registry.register(ExtractorTool(extractor=extractor))
    tool_registry.register(LLMCandidateTool())
    tool_registry.register(AdvantageDictionaryTool())
    tool_registry.register(ContactMissingRuleTool())
    tool_registry.register(EducationMissingRuleTool())
    tool_registry.register(YearsExperienceRuleTool())
    tool_registry.register(KeywordMatchRuleTool())
    return AuditJobService(
        repository=SQLiteAuditJobRepository(Path(settings.storage_dir) / "audit_jobs.sqlite3"),
        use_case=AuditUseCase(
            parser=FakeDocumentParser(),
            extractor=extractor,
            normalizer=FindingNormalizer(),
            tool_registry=tool_registry,
            job_template=JobTemplate.sample_frontend(),
        ),
    )