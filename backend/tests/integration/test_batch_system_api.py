from datetime import datetime, timezone

from fastapi.testclient import TestClient

from auditx.api.dependencies import (
    get_batch_evidence_repository,
    get_batch_review_service,
    get_candidate_query_service,
    get_resume_library_service,
)
from auditx.domain.candidate import CandidateProfile, CandidateScoreRecord
from auditx.domain.evidence_index import EvidenceIndexRecord
from auditx.domain.scoring import CandidateLayer
from auditx.main import create_app

FIXTURES_DIR = "backend/tests/fixtures"


def test_resumes_api_imports_and_lists_resume_metadata() -> None:
    _clear_batch_service_caches()
    client = TestClient(create_app())

    response = client.post(
        "/api/resumes/import",
        json={
            "resume_id": "resume_1",
            "filename": "ada.pdf",
            "parsed_document_artifact_uri": "local://artifacts/jobs/job_1/parsed.json",
            "imported_at": "2026-05-20T00:00:00Z",
        },
    )
    list_response = client.get("/api/resumes", params={"status": "new"})

    assert response.status_code == 200
    assert response.json()["parsed_document_id"] == "local://artifacts/jobs/job_1/parsed.json"
    assert list_response.status_code == 200
    assert [resume["resume_id"] for resume in list_response.json()["resumes"]] == ["resume_1"]


def test_candidates_api_lists_seeded_candidates_and_top_n() -> None:
    _clear_batch_service_caches()
    service = get_candidate_query_service()
    service.repository.save_profile(
        CandidateProfile(
            candidate_id="candidate_1",
            resume_id="resume_1",
            display_name="Ada Lovelace",
            created_at=_now(),
            updated_at=_now(),
        )
    )
    service.repository.save_score(
        CandidateScoreRecord(
            score_id="score_1",
            candidate_id="candidate_1",
            review_session_id="review_1",
            template_id="frontend_engineer",
            template_version="v1",
            total_score=91,
            layer=CandidateLayer.best,
            created_at=_now(),
        )
    )
    client = TestClient(create_app())

    list_response = client.get("/api/candidates", params={"layer": "best"})
    top_response = client.get("/api/candidates/top-n", params={"limit": 1})

    assert list_response.status_code == 200
    assert list_response.json()["candidates"][0]["profile"]["candidate_id"] == "candidate_1"
    assert top_response.status_code == 200
    assert top_response.json()["candidates"][0]["latest_score"]["total_score"] == 91


def test_candidates_api_returns_candidate_detail_with_findings_scores_and_evidence() -> None:
    _clear_batch_service_caches()
    service = get_candidate_query_service()
    evidence_repository = get_batch_evidence_repository()
    service.repository.save_profile(
        CandidateProfile(
            candidate_id="candidate_1",
            resume_id="resume_1",
            display_name="Ada Lovelace",
            created_at=_now(),
            updated_at=_now(),
        )
    )
    service.repository.save_score(
        CandidateScoreRecord(
            score_id="score_1",
            candidate_id="candidate_1",
            review_session_id="review_1",
            template_id="frontend_engineer",
            template_version="v1",
            total_score=91,
            layer=CandidateLayer.best,
            created_at=_now(),
        )
    )
    evidence_repository.save(
        EvidenceIndexRecord(
            evidence_id="evidence_1",
            candidate_id="candidate_1",
            resume_id="resume_1",
            parsed_document_artifact_uri="local://artifacts/jobs/job_1/parsed.json",
            page_number=1,
            block_id="block_1",
            text_excerpt="React TypeScript",
            created_at=_now(),
        )
    )
    client = TestClient(create_app())

    detail_response = client.get("/api/candidates/candidate_1")
    evidence_response = client.get("/api/candidates/candidate_1/evidence")

    assert detail_response.status_code == 200
    assert detail_response.json()["profile"]["candidate_id"] == "candidate_1"
    assert detail_response.json()["scores"][0]["score_id"] == "score_1"
    assert evidence_response.status_code == 200
    assert evidence_response.json()["evidence"][0]["evidence_id"] == "evidence_1"


def test_candidates_api_returns_404_for_missing_candidate_detail() -> None:
    _clear_batch_service_caches()
    client = TestClient(create_app())

    response = client.get("/api/candidates/missing_candidate")

    assert response.status_code == 404
    assert response.json()["detail"] == "Candidate not found"


def test_batches_api_creates_batch_adds_candidate_and_marks_failure_in_item_only() -> None:
    _clear_batch_service_caches()
    client = TestClient(create_app())

    create_response = client.post(
        "/api/batches",
        json={
            "batch_id": "batch_1",
            "name": "Frontend Batch",
            "job_template_id": "frontend_engineer",
            "created_at": "2026-05-20T00:00:00Z",
        },
    )
    add_response = client.post(
        "/api/batches/batch_1/candidates",
        json={"candidate_id": "candidate_1", "created_at": "2026-05-20T00:00:00Z"},
    )
    fail_response = client.post(
        "/api/batches/batch_1/candidates/candidate_1/fail",
        json={"error": "OCR failed", "updated_at": "2026-05-20T00:00:00Z"},
    )
    detail_response = client.get("/api/batches/batch_1")

    assert create_response.status_code == 200
    assert add_response.status_code == 200
    assert fail_response.status_code == 200
    assert fail_response.json()["status"] == "failed"
    assert detail_response.status_code == 200
    assert detail_response.json()["batch"]["status"] == "draft"
    assert detail_response.json()["candidates"][0]["error"] == "OCR failed"


def test_batches_api_reranks_candidates_and_returns_top_n() -> None:
    _clear_batch_service_caches()
    candidate_service = get_candidate_query_service()
    candidate_service.repository.save_score(
        CandidateScoreRecord(
            score_id="score_1",
            candidate_id="candidate_1",
            review_session_id="review_1",
            template_id="frontend_engineer",
            template_version="v1",
            total_score=80,
            layer=CandidateLayer.potential,
            risk_count=0,
            created_at=_now(),
        )
    )
    candidate_service.repository.save_score(
        CandidateScoreRecord(
            score_id="score_2",
            candidate_id="candidate_2",
            review_session_id="review_2",
            template_id="frontend_engineer",
            template_version="v1",
            total_score=95,
            layer=CandidateLayer.best,
            risk_count=0,
            created_at=_now(),
        )
    )
    client = TestClient(create_app())
    client.post(
        "/api/batches",
        json={
            "batch_id": "batch_rank",
            "name": "Ranking Batch",
            "job_template_id": "frontend_engineer",
            "created_at": "2026-05-20T00:00:00Z",
        },
    )
    for candidate_id in ["candidate_1", "candidate_2"]:
        client.post(
            "/api/batches/batch_rank/candidates",
            json={"candidate_id": candidate_id, "created_at": "2026-05-20T00:00:00Z"},
        )

    rerank_response = client.post(
        "/api/batches/batch_rank/rerank",
        json={"top_n": 1, "updated_at": "2026-05-20T00:00:00Z"},
    )
    top_response = client.get("/api/batches/batch_rank/top-n", params={"limit": 1})

    assert rerank_response.status_code == 200
    assert rerank_response.json()["batch"]["status"] == "completed"
    assert rerank_response.json()["candidates"][0]["candidate_id"] == "candidate_2"
    assert rerank_response.json()["candidates"][0]["rank"] == 1
    assert top_response.status_code == 200
    assert top_response.json()["candidates"][0]["candidate_id"] == "candidate_2"


def test_completed_audit_job_is_visible_in_candidates_api(monkeypatch) -> None:
    monkeypatch.setenv("AUDITX_OCR_PROVIDER", "fake")
    monkeypatch.setenv("AUDITX_STORAGE_DIR", "backend/tests/.repo_tmp/batch_index_api")
    from auditx.config.settings import get_settings
    from auditx.api.dependencies import get_audit_job_service

    get_settings.cache_clear()
    get_audit_job_service.cache_clear()
    _clear_batch_service_caches()
    client = TestClient(create_app())

    create_response = client.post(
        "/api/audit-jobs",
        json={"file_path": f"{FIXTURES_DIR}/demo_resume.pdf"},
    )
    job_response = client.get(f"/api/audit-jobs/{create_response.json()['job_id']}")
    candidates_response = client.get("/api/candidates")

    assert create_response.status_code == 200
    assert job_response.json()["status"] == "completed"
    assert candidates_response.status_code == 200
    assert candidates_response.json()["candidates"][0]["profile"]["candidate_id"].startswith(
        "candidate_"
    )


def _clear_batch_service_caches() -> None:
    get_resume_library_service.cache_clear()
    get_candidate_query_service.cache_clear()
    get_batch_evidence_repository.cache_clear()
    get_batch_review_service.cache_clear()


def _now() -> datetime:
    return datetime(2026, 5, 20, tzinfo=timezone.utc)
