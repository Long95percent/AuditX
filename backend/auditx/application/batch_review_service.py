from datetime import datetime
from pathlib import Path
from uuid import uuid4

from auditx.domain.batch import BatchCandidate, BatchCandidateStatus, BatchRecord, BatchStatus
from auditx.domain.candidate import CandidateProfile
from auditx.infrastructure.storage.batch_repository import InMemoryBatchRepository
from auditx.infrastructure.storage.candidate_repository import InMemoryCandidateRepository
from auditx.infrastructure.storage.evidence_repository import InMemoryEvidenceRepository
from auditx.infrastructure.storage.resume_repository import InMemoryResumeRepository


class BatchReviewService:
    def __init__(
        self,
        repository: InMemoryBatchRepository,
        candidate_repository: InMemoryCandidateRepository | None = None,
        evidence_repository: InMemoryEvidenceRepository | None = None,
        resume_repository: InMemoryResumeRepository | None = None,
        audit_job_service=None,
    ) -> None:
        self.repository = repository
        self.candidate_repository = candidate_repository
        self.evidence_repository = evidence_repository
        self.resume_repository = resume_repository
        self.audit_job_service = audit_job_service

    def create_batch(
        self,
        batch_id: str,
        name: str,
        job_template_id: str,
        created_at: datetime,
    ) -> BatchRecord:
        batch = BatchRecord(
            batch_id=batch_id,
            name=name,
            status=BatchStatus.draft,
            job_template_id=job_template_id,
            created_at=created_at,
            updated_at=created_at,
        )
        self.repository.save_batch(batch)
        return batch

    def get_batch(self, batch_id: str) -> BatchRecord | None:
        return self.repository.get_batch(batch_id)

    def list_batches(self) -> list[BatchRecord]:
        return self.repository.list_batches()

    def add_candidate(
        self,
        batch_id: str,
        candidate_id: str,
        created_at: datetime,
    ) -> BatchCandidate:
        candidate = BatchCandidate(
            batch_id=batch_id,
            candidate_id=candidate_id,
            status=BatchCandidateStatus.pending,
            created_at=created_at,
            updated_at=created_at,
        )
        self.repository.save_candidate(candidate)
        return candidate

    def import_files(
        self,
        batch_id: str,
        file_paths: list[str],
        imported_at: datetime,
    ) -> list[BatchCandidate]:
        imported_candidates = []
        for file_path in file_paths:
            candidate_id = f"candidate_import_{uuid4().hex}"
            resume_id = f"resume_import_{uuid4().hex}"
            if self.candidate_repository is not None:
                self.candidate_repository.save_profile(
                    CandidateProfile(
                        candidate_id=candidate_id,
                        resume_id=resume_id,
                        display_name=Path(file_path).stem or candidate_id,
                        source_file_path=file_path,
                        source_document_artifact_uri=None,
                        summary=f"Imported from {Path(file_path).name}; pending review run.",
                        tags=["imported"],
                        created_at=imported_at,
                        updated_at=imported_at,
                    )
                )
            imported_candidates.append(self.add_candidate(batch_id, candidate_id, imported_at))
        return imported_candidates

    def list_candidates(self, batch_id: str) -> list[BatchCandidate]:
        return self.repository.list_candidates(batch_id)

    def mark_candidate_failed(
        self,
        batch_id: str,
        candidate_id: str,
        error: str,
        updated_at: datetime,
    ) -> BatchCandidate:
        candidate = self.repository.get_candidate(batch_id, candidate_id)
        if candidate is None:
            candidate = BatchCandidate(
                batch_id=batch_id,
                candidate_id=candidate_id,
                status=BatchCandidateStatus.pending,
                created_at=updated_at,
                updated_at=updated_at,
            )
        failed = candidate.model_copy(
            update={
                "status": BatchCandidateStatus.failed,
                "error": error,
                "updated_at": updated_at,
            }
        )
        self.repository.save_candidate(failed)
        return failed

    def run_pending(self, batch_id: str, updated_at: datetime) -> list[BatchCandidate]:
        if self.audit_job_service is None or self.candidate_repository is None:
            raise ValueError("audit_job_service and candidate_repository are required to run a batch")
        results = []
        for candidate in self.repository.list_candidates(batch_id):
            if candidate.status not in {BatchCandidateStatus.pending, BatchCandidateStatus.failed}:
                continue
            profile = self.candidate_repository.get_profile(candidate.candidate_id)
            if profile is None:
                results.append(
                    self.mark_candidate_failed(batch_id, candidate.candidate_id, "Candidate profile not found", updated_at)
                )
                continue
            if profile.source_document_artifact_uri:
                results.append(candidate)
                continue
            try:
                if not profile.source_file_path:
                    raise RuntimeError("Candidate source file path not found")
                job = self.audit_job_service.create_and_run(profile.source_file_path)
                if job.status == "failed":
                    raise RuntimeError(job.error or "Audit job failed")
                self._merge_indexed_review(candidate.candidate_id, job.job_id)
                updated = candidate.model_copy(
                    update={
                        "status": BatchCandidateStatus.reviewed,
                        "error": None,
                        "updated_at": updated_at,
                    }
                )
                self.repository.save_candidate(updated)
                results.append(updated)
            except Exception as exc:
                results.append(
                    self.mark_candidate_failed(batch_id, candidate.candidate_id, str(exc), updated_at)
                )
        return results

    def retry_failed(self, batch_id: str, updated_at: datetime) -> list[BatchCandidate]:
        retried = []
        for candidate in self.repository.list_candidates(batch_id):
            if candidate.status != BatchCandidateStatus.failed:
                continue
            reset = candidate.model_copy(
                update={
                    "status": BatchCandidateStatus.pending,
                    "error": None,
                    "updated_at": updated_at,
                }
            )
            self.repository.save_candidate(reset)
            retried.append(reset)
        return retried

    def _merge_indexed_review(self, target_candidate_id: str, job_id: str) -> None:
        if self.candidate_repository is None:
            return
        indexed_candidate_id = f"candidate_{job_id}"
        indexed_profile = self.candidate_repository.get_profile(indexed_candidate_id)
        target_profile = self.candidate_repository.get_profile(target_candidate_id)
        if indexed_profile is not None and target_profile is not None:
            self.candidate_repository.save_profile(
                indexed_profile.model_copy(
                    update={
                        "candidate_id": target_candidate_id,
                        "resume_id": target_profile.resume_id,
                        "display_name": target_profile.display_name,
                    }
                )
            )
        for score in self.candidate_repository.list_scores(indexed_candidate_id):
            self.candidate_repository.save_score(
                score.model_copy(
                    update={
                        "score_id": f"score_{target_candidate_id}_{score.score_id}",
                        "candidate_id": target_candidate_id,
                    }
                )
            )
        for finding in self.candidate_repository.list_findings(indexed_candidate_id):
            self.candidate_repository.save_finding(
                finding.model_copy(
                    update={
                        "finding_id": f"finding_{target_candidate_id}_{finding.finding_id}",
                        "candidate_id": target_candidate_id,
                    }
                )
            )
        if self.evidence_repository is None:
            return
        for evidence in self.evidence_repository.list_by_candidate(indexed_candidate_id):
            self.evidence_repository.save(
                evidence.model_copy(
                    update={
                        "evidence_id": f"evidence_{target_candidate_id}_{evidence.evidence_id}",
                        "candidate_id": target_candidate_id,
                    }
                )
            )

    def rerank(self, batch_id: str, top_n: int, updated_at: datetime) -> list[BatchCandidate]:
        if self.candidate_repository is None:
            raise ValueError("candidate_repository is required to rerank a batch")
        if top_n <= 0:
            raise ValueError("top_n must be greater than 0")
        batch = self.repository.get_batch(batch_id)
        if batch is None:
            return []
        ranked_inputs = []
        for candidate in self.repository.list_candidates(batch_id):
            if candidate.status == BatchCandidateStatus.failed:
                continue
            latest_score = self._latest_score(candidate.candidate_id)
            if latest_score is None:
                ranked_inputs.append((candidate, None))
            else:
                ranked_inputs.append((candidate, latest_score))
        ranked_inputs.sort(key=self._ranking_key)
        ranked_candidates = []
        for index, (candidate, score) in enumerate(ranked_inputs, start=1):
            if score is None:
                updated = candidate.model_copy(
                    update={
                        "status": BatchCandidateStatus.eliminated,
                        "rank": index,
                        "score_id": None,
                        "included_reason": None,
                        "eliminated_reason": "missing_score",
                        "updated_at": updated_at,
                    }
                )
            elif index <= top_n:
                updated = candidate.model_copy(
                    update={
                        "status": BatchCandidateStatus.shortlisted,
                        "rank": index,
                        "score_id": score.score_id,
                        "included_reason": self._included_reason(index, score.total_score, score.risk_count),
                        "eliminated_reason": None,
                        "updated_at": updated_at,
                    }
                )
            else:
                updated = candidate.model_copy(
                    update={
                        "status": BatchCandidateStatus.eliminated,
                        "rank": index,
                        "score_id": score.score_id,
                        "included_reason": None,
                        "eliminated_reason": self._eliminated_reason(
                            top_n, index, score.total_score, score.risk_count
                        ),
                        "updated_at": updated_at,
                    }
                )
            self.repository.save_candidate(updated)
            ranked_candidates.append(updated)
        completed = batch.model_copy(
            update={"status": BatchStatus.completed, "updated_at": updated_at}
        )
        self.repository.save_batch(completed)
        return ranked_candidates

    def top_n(self, batch_id: str, limit: int) -> list[BatchCandidate]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        return [
            candidate
            for candidate in sorted(
                self.repository.list_candidates(batch_id),
                key=lambda item: item.rank if item.rank is not None else 10**9,
            )
            if candidate.status == BatchCandidateStatus.shortlisted
        ][:limit]

    def _latest_score(self, candidate_id: str):
        if self.candidate_repository is None:
            return None
        scores = self.candidate_repository.list_scores(candidate_id=candidate_id)
        if not scores:
            return None
        return sorted(scores, key=lambda score: score.created_at, reverse=True)[0]

    def _ranking_key(self, item) -> tuple[float, int, str]:
        candidate, score = item
        if score is None:
            return (float("inf"), 10**9, candidate.candidate_id)
        return (-score.total_score, score.risk_count, candidate.candidate_id)

    def _included_reason(self, rank: int, total_score: float, risk_count: int) -> str:
        return f"rank={rank} score={total_score:.1f} risk_count={risk_count}"

    def _eliminated_reason(
        self,
        top_n: int,
        rank: int,
        total_score: float,
        risk_count: int,
    ) -> str:
        return f"outside_top_{top_n} rank={rank} score={total_score:.1f} risk_count={risk_count}"
