from fastapi.testclient import TestClient

from src.api import app

client = TestClient(app)


def test_health_returns_success():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_unknown_agent_fail_with_400():
    response = client.post("/analyze", json={"file_content": "x=1", "agent": "UNKNOWN"})
    assert response.status_code == 400


def test_analyze_code_style_clean_success():
    response = client.post(
        "/analyze",
        json={"file_content": "x = 1\n", "agent": "CODE_STYLE"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "issues" in data
    assert "suggestions" in data


def test_analyze_code_style_issues_success_with_issues_and_suggestions():
    bad_code = "x=1\ny=2\n"
    response = client.post(
        "/analyze",
        json={"file_content": bad_code, "agent": "CODE_STYLE"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["issues"], list)
    assert isinstance(data["suggestions"], list)
