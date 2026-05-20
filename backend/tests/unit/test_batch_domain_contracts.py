from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from auditx.domain.batch import BatchCandidate, BatchCandidateStatus, BatchRecord, BatchStatus
from auditx.domain.candidate import CandidateFindingRecord, CandidateProfile, CandidateScoreRecord
from auditx.domain.evidence_index import EvidenceIndexRecord
from auditx.domain.scoring import CandidateLayer


def test_candidate_profile_keeps_structured_summary_without_large_document_payload() -> None:
    profile = CandidateProfile(
        candidate_id="candidate_1",
        resume_id="resume_1",
        display_name="Ada Lovelace",
        source_document_artifact_uri="local://artifacts/jobs/job_1/source.pdf",
        created_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
        summary="Frontend engineer with OCR evidence.",
        skills=["React", "TypeScript"],
        tags=["frontend"],
    )

    assert profile.candidate_id == "candidate_1"
    assert profile.resume_id == "resume_1"
    assert "full_text" not in CandidateProfile.model_fields
    assert "parsed_document" not in CandidateProfile.model_fields
    assert profile.skills == ["React", "TypeScript"]


def test_candidate_score_record_is_batch_independent_score_snapshot() -> None:
    score = CandidateScoreRecord(
        score_id="score_1",
        candidate_id="candidate_1",
        review_session_id="review_1",
        template_id="frontend_engineer",
        template_version="v1",
        total_score=88.5,
        layer=CandidateLayer.best,
        dimension_scores={"ability_match": 90},
        advantage_tags=["React"],
        risk_count=1,
        created_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )

    assert score.batch_id is None
    assert score.total_score == 88.5
    assert score.layer == CandidateLayer.best


def test_candidate_finding_record_points_to_evidence_index_instead_of_copying_ocr_raw() -> None:
    finding = CandidateFindingRecord(
        finding_id="finding_1",
        candidate_id="candidate_1",
        review_session_id="review_1",
        title="Employment gap",
        risk_level="medium",
        confidence=0.8,
        evidence_ids=["evidence_1"],
        created_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )

    assert finding.evidence_ids == ["evidence_1"]
    assert "ocr_raw" not in CandidateFindingRecord.model_fields


def test_evidence_index_record_stores_lightweight_location_and_artifact_reference() -> None:
    evidence = EvidenceIndexRecord(
        evidence_id="evidence_1",
        candidate_id="candidate_1",
        resume_id="resume_1",
        parsed_document_artifact_uri="local://artifacts/jobs/job_1/parsed.json",
        page_number=1,
        block_id="block_1",
        text_excerpt="React TypeScript 5 years",
        bbox={"x0": 10, "y0": 20, "x1": 100, "y1": 40},
        created_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )

    assert evidence.text_excerpt == "React TypeScript 5 years"
    assert "parsed_document" not in EvidenceIndexRecord.model_fields
    assert "ocr_raw" not in EvidenceIndexRecord.model_fields


def test_batch_record_and_candidate_keep_batch_state_separate_from_audit_job_payload() -> None:
    batch = BatchRecord(
        batch_id="batch_1",
        name="Frontend May Screening",
        status=BatchStatus.draft,
        job_template_id="frontend_engineer",
        created_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )
    candidate = BatchCandidate(
        batch_id="batch_1",
        candidate_id="candidate_1",
        status=BatchCandidateStatus.pending,
        rank=None,
        score_id=None,
        included_reason=None,
        eliminated_reason=None,
        error=None,
        created_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
    )

    assert batch.status == BatchStatus.draft
    assert candidate.status == BatchCandidateStatus.pending
    assert "audit_job_payload" not in BatchRecord.model_fields
    assert "audit_job_payload" not in BatchCandidate.model_fields


def test_batch_candidate_cannot_have_rank_less_than_one() -> None:
    with pytest.raises(ValidationError):
        BatchCandidate(
            batch_id="batch_1",
            candidate_id="candidate_1",
            status=BatchCandidateStatus.shortlisted,
            rank=0,
            created_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            updated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
        )
