from datetime import datetime
from pathlib import Path

from auditx.application.audit_job_service import AuditJob, AuditJobStatus
from auditx.domain.candidate import CandidateFindingRecord, CandidateProfile, CandidateScoreRecord
from auditx.domain.evidence_index import EvidenceIndexRecord
from auditx.domain.resume_library import ResumeRecord, ResumeStatus


class ReviewResultIndexer:
    def __init__(self, resume_repository, candidate_repository, evidence_repository) -> None:
        self.resume_repository = resume_repository
        self.candidate_repository = candidate_repository
        self.evidence_repository = evidence_repository

    def index_completed_job(self, job: AuditJob, indexed_at: datetime) -> None:
        if job.status != AuditJobStatus.completed:
            return
        resume_id = self._resume_id(job)
        candidate_id = self._candidate_id(job)
        parsed_document_artifact_uri = self._artifact_uri(job, "parsed_document")
        source_document_artifact_uri = self._artifact_uri(job, "source_document")
        self.resume_repository.save(
            ResumeRecord(
                resume_id=resume_id,
                filename=Path(job.file_path).name,
                imported_at=indexed_at,
                status=ResumeStatus.reviewed,
                parsed_document_id=parsed_document_artifact_uri,
            )
        )
        self.candidate_repository.save_profile(
            CandidateProfile(
                candidate_id=candidate_id,
                resume_id=resume_id,
                display_name=Path(job.file_path).stem or candidate_id,
                source_file_path=job.file_path,
                source_document_artifact_uri=source_document_artifact_uri,
                review_session_id=job.job_id,
                summary=f"Indexed from audit job {job.job_id}",
                created_at=indexed_at,
                updated_at=indexed_at,
            )
        )
        if job.score is not None:
            self.candidate_repository.save_score(
                CandidateScoreRecord(
                    score_id=f"score_{job.job_id}",
                    candidate_id=candidate_id,
                    review_session_id=job.job_id,
                    template_id=job.score.template_id,
                    template_version=job.score.template_version,
                    total_score=job.score.total_score,
                    layer=job.score.layer,
                    dimension_scores=job.score.dimension_scores,
                    advantage_tags=job.score.advantage_tags,
                    risk_count=job.score.risk_count,
                    created_at=job.score.created_at,
                )
            )
        for finding in job.findings:
            evidence_ids = []
            for index, evidence in enumerate(finding.evidences):
                evidence_id = f"evidence_{finding.finding_id}_{index}"
                evidence_ids.append(evidence_id)
                self.evidence_repository.save(
                    EvidenceIndexRecord(
                        evidence_id=evidence_id,
                        candidate_id=candidate_id,
                        resume_id=resume_id,
                        parsed_document_artifact_uri=parsed_document_artifact_uri or "unavailable",
                        page_number=evidence.page_number,
                        block_id=evidence.block_id,
                        text_excerpt=evidence.quote,
                        bbox=evidence.bbox.model_dump(),
                        created_at=indexed_at,
                    )
                )
            self.candidate_repository.save_finding(
                CandidateFindingRecord(
                    finding_id=finding.finding_id,
                    candidate_id=candidate_id,
                    review_session_id=job.job_id,
                    title=finding.title,
                    risk_level=finding.risk_level.value,
                    confidence=finding.confidence,
                    evidence_ids=evidence_ids,
                    created_at=indexed_at,
                )
            )

    def _artifact_uri(self, job: AuditJob, artifact_type: str) -> str | None:
        artifact = next(
            (artifact for artifact in job.artifacts if artifact.artifact_type == artifact_type),
            None,
        )
        if artifact is None:
            return None
        return artifact.artifact_uri

    def _resume_id(self, job: AuditJob) -> str:
        return f"resume_{job.job_id}"

    def _candidate_id(self, job: AuditJob) -> str:
        return f"candidate_{job.job_id}"
