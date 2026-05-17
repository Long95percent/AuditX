from fastapi.testclient import TestClient

from auditx.main import create_app


def test_audit_job_api_creates_job_and_returns_findings() -> None:
    client = TestClient(create_app())

    create_response = client.post(
        "/api/audit-jobs",
        json={"file_path": "demo_resume.pdf"},
    )

    assert create_response.status_code == 200
    payload = create_response.json()
    assert payload["status"] == "completed"
    assert payload["document_id"] == "fake_doc_001"
    assert len(payload["findings"]) == 1

    job_id = payload["job_id"]
    job_response = client.get(f"/api/audit-jobs/{job_id}")
    findings_response = client.get(f"/api/audit-jobs/{job_id}/findings")

    assert job_response.status_code == 200
    assert job_response.json()["job_id"] == job_id
    assert findings_response.status_code == 200
    assert findings_response.json()["findings"][0]["rule_id"] == "hr.timeline.fake_risk"
