from fastapi.testclient import TestClient

from auditx.main import create_app


def test_audit_api_allows_vite_desktop_origin_preflight() -> None:
    client = TestClient(create_app())

    response = client.options(
        "/api/audit-jobs",
        headers={
            "Origin": "http://127.0.0.1:1420",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:1420"
    assert "POST" in response.headers["access-control-allow-methods"]
