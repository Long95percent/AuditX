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
    assert len(payload["findings"]) == 1

    job_id = payload["job_id"]
    job_response = client.get(f"/api/audit-jobs/{job_id}")
    findings_response = client.get(f"/api/audit-jobs/{job_id}/findings")

    assert job_response.status_code == 200
    assert job_response.json()["job_id"] == job_id
    assert findings_response.status_code == 200
    assert findings_response.json()["findings"][0]["rule_id"] == "hr.timeline.fake_risk"


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
