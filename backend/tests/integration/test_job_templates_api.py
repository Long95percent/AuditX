from fastapi.testclient import TestClient

from auditx.main import create_app


def test_job_template_api_rejects_generation_without_openai_key() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/job-templates/from-jd",
        json={"job_name": "增长产品经理", "jd": "负责增长策略和用户研究"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "OpenAI API key is not configured"


def test_openai_settings_api_accepts_key_without_echoing_secret() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/settings/openai",
        json={"api_key": "sk-test", "model": "gpt-5.4-mini"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["configured"] is True
    assert payload["api_key"] is None
    assert payload["model"] == "gpt-5.4-mini"
