from functools import lru_cache

from auditx.agent_core.fake_extractor import FakeExtractor
from auditx.agent_core.finding_normalizer import FindingNormalizer
from auditx.application.audit_job_service import AuditJobService
from auditx.application.audit_use_case import AuditUseCase
from auditx.document_pipeline.fake_parser import FakeDocumentParser


@lru_cache(maxsize=1)
def get_audit_job_service() -> AuditJobService:
    return AuditJobService(
        use_case=AuditUseCase(
            parser=FakeDocumentParser(),
            extractor=FakeExtractor(),
            normalizer=FindingNormalizer(),
        )
    )
