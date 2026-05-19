from pathlib import Path

from fastapi.testclient import TestClient

from auditx.main import create_app

FIXTURES_DIR = Path("backend/tests/fixtures")


def test_audit_job_api_creates_job_and_returns_findings() -> None:
    client = TestClient(create_app())
    document_path = FIXTURES_DIR / "demo_resume.pdf"

    create_response = client.post(
        "/api/audit-jobs",
        json={"file_path": str(document_path)},
    )

    assert create_response.status_code == 200
    payload = create_response.json()
    assert payload["status"] == "completed"
    assert payload["file_path"] == str(document_path)
    assert payload["document_id"] == "fake_doc_001"
    assert len(payload["findings"]) == 2
    assert len(payload["candidates"]) == 4
    rejected_candidate_ids = {
        candidate["candidate_id"] for candidate in payload["rejected_candidates"]
    }
    assert "llm_candidate_unverified_gap" in rejected_candidate_ids
    assert "rule_contact_missing" in rejected_candidate_ids
    assert payload["trace"]["steps"][0]["step_type"] == "tool"
    assert payload["trace"]["steps"][0]["metadata"]["tool_name"] == "agent.extractor.fake"
    assert any(
        step["name"] == "agent.llm_mock.candidate_discovery"
        for step in payload["trace"]["steps"]
    )
    assert any(
        step["name"] == "resume.rule.contact_missing"
        for step in payload["trace"]["steps"]
    )

    job_id = payload["job_id"]
    job_response = client.get(f"/api/audit-jobs/{job_id}")
    findings_response = client.get(f"/api/audit-jobs/{job_id}/findings")

    assert job_response.status_code == 200
    assert job_response.json()["job_id"] == job_id
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
