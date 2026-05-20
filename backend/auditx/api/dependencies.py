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
from auditx.document_pipeline.base import DocumentParser
from auditx.document_pipeline.fake_parser import FakeDocumentParser
from auditx.document_pipeline.paddleocr_parser import PaddleOCRDocumentParser
from auditx.domain.scoring import JobTemplate
from auditx.infrastructure.storage.audit_job_repository import SQLiteAuditJobRepository
from auditx.infrastructure.storage.artifact_store import FileSystemArtifactStore
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
        artifact_store=FileSystemArtifactStore(Path(settings.storage_dir) / "artifacts"),
        use_case=AuditUseCase(
            parser=build_document_parser(settings.ocr_provider),
            extractor=extractor,
            normalizer=FindingNormalizer(),
            tool_registry=tool_registry,
            job_template=JobTemplate.sample_frontend(),
        ),
    )


def build_document_parser(ocr_provider: str) -> DocumentParser:
    if ocr_provider == "fake":
        return FakeDocumentParser()
    if ocr_provider == "paddleocr":
        return PaddleOCRDocumentParser()
    raise ValueError(f"Unsupported OCR provider: {ocr_provider}")
