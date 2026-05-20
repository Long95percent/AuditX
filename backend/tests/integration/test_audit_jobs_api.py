import json
from pathlib import Path

from fastapi.testclient import TestClient

from auditx.config.settings import get_settings
from auditx.main import create_app

FIXTURES_DIR = Path("backend/tests/fixtures")


def test_audit_job_api_creates_job_task_and_returns_findings() -> None:
    client = TestClient(create_app())
    document_path = FIXTURES_DIR / "demo_resume.pdf"

    create_response = client.post(
        "/api/audit-jobs",
        json={"file_path": str(document_path)},
    )

    assert create_response.status_code == 200
    payload = create_response.json()
    assert payload["status"] in {"pending", "running", "completed"}
    assert payload["file_path"] == str(document_path.resolve())

    job_id = payload["job_id"]
    job_response = client.get(f"/api/audit-jobs/{job_id}")
    findings_response = client.get(f"/api/audit-jobs/{job_id}/findings")

    assert job_response.status_code == 200
    job_payload = job_response.json()
    assert job_payload["job_id"] == job_id
    assert job_payload["status"] == "completed"
    assert job_payload["document_id"] == "fake_doc_001"
    assert len(job_payload["findings"]) == 2
    assert len(job_payload["candidates"]) == 4
    assert job_payload["score"]["total_score"] >= 0
    assert job_payload["score"]["layer"] in {"best", "potential", "not_recommended"}
    assert job_payload["score"]["dimension_scores"]
    assert isinstance(job_payload["score"]["advantage_tags"], list)
    assert job_payload["score"]["calculation_details"]
    first_finding = job_payload["findings"][0]
    first_evidence = first_finding["evidences"][0]
    assert first_evidence["quote"]
    assert first_evidence["page_number"] >= 1
    assert first_evidence["block_id"]
    assert set(first_evidence["bbox"]) == {"x0", "y0", "x1", "y1"}
    rejected_candidate_ids = {
        candidate["candidate_id"] for candidate in job_payload["rejected_candidates"]
    }
    assert "llm_candidate_unverified_gap" in rejected_candidate_ids
    assert "rule_contact_missing" in rejected_candidate_ids
    rejected_by_id = {
        candidate["candidate_id"]: candidate for candidate in job_payload["rejected_candidates"]
    }
    assert rejected_by_id["llm_candidate_unverified_gap"]["rejection_reason"] == "missing verified evidence"
    assert rejected_by_id["rule_contact_missing"]["rejection_reason"] == "missing verified evidence"
    assert job_payload["trace"]["steps"][0]["step_type"] == "tool"
    assert job_payload["trace"]["steps"][0]["metadata"]["tool_name"] == "agent.extractor.fake"
    assert any(
        step["name"] == "agent.llm_mock.candidate_discovery"
        for step in job_payload["trace"]["steps"]
    )
    assert any(
        step["name"] == "resume.rule.contact_missing"
        for step in job_payload["trace"]["steps"]
    )
    assert any(
        step["name"] == "candidate_evidence_gate" and step["status"] == "rejected"
        for step in job_payload["trace"]["steps"]
    )
    assert any(
        step["name"] == "scoring_engine.score" and step["metadata"].get("calculation_details")
        for step in job_payload["trace"]["steps"]
    )
    assert findings_response.status_code == 200
    returned_rule_ids = {finding["rule_id"] for finding in findings_response.json()["findings"]}
    assert "hr.timeline.fake_risk" in returned_rule_ids


def test_audit_job_api_rejects_missing_file() -> None:
    client = TestClient(create_app())
    missing_path = FIXTURES_DIR / "missing.pdf"

    response = client.post(
        "/api/audit-jobs",
        json={"file_path": str(missing_path)},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Selected document does not exist"


def test_audit_job_api_rejects_directory() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/audit-jobs",
        json={"file_path": str(FIXTURES_DIR)},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Selected document is not a file"


def test_audit_job_api_rejects_file_outside_allowed_roots(monkeypatch) -> None:
    monkeypatch.setenv("AUDITX_ALLOWED_DOCUMENT_ROOTS", json.dumps([str(FIXTURES_DIR.resolve())]))
    get_settings.cache_clear()
    try:
        client = TestClient(create_app())

        response = client.post(
            "/api/audit-jobs",
            json={"file_path": str(Path("README.md").resolve())},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Selected document is outside allowed document roots"
    finally:
        get_settings.cache_clear()

def test_audit_job_api_persists_job_across_service_recreation(monkeypatch) -> None:
    monkeypatch.setenv("AUDITX_STORAGE_DIR", "backend/tests/.repo_tmp/api_persistence")
    get_settings.cache_clear()
    from auditx.api.dependencies import get_audit_job_service

    get_audit_job_service.cache_clear()
    try:
        first_client = TestClient(create_app())
        document_path = FIXTURES_DIR / "demo_resume.pdf"
        create_response = first_client.post(
            "/api/audit-jobs",
            json={"file_path": str(document_path)},
        )
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        get_audit_job_service.cache_clear()
        second_client = TestClient(create_app())
        response = second_client.get(f"/api/audit-jobs/{job_id}")

        assert response.status_code == 200
        assert response.json()["job_id"] == job_id
        assert response.json()["status"] == "completed"
    finally:
        get_audit_job_service.cache_clear()
        get_settings.cache_clear()
