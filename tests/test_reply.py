from fastapi.testclient import TestClient
import pytest

from app.main import create_app
from app.core.config import reset_settings_cache
from app.middleware.rate_limit import reset_rate_limit_cache


@pytest.fixture()
def client(monkeypatch):
    """
    Build a fresh app/client per test so env changes (API key) apply.
    """
    reset_settings_cache()
    reset_rate_limit_cache()
    return TestClient(create_app())


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_draft_endpoint_returns_three_drafts(client):
    payload = {
        "message": "Can you share the latest metrics for Q1?",
        "channel": "email",
        "tone": "professional",
    }
    response = client.post("/v1/reply/draft", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["drafts"]) == 3
    assert data["requested_tone"] == "professional"


def test_auth_required_when_api_key_configured(monkeypatch, client):
    monkeypatch.setenv("SMART_REPLY_API_KEY", "secret")
    reset_settings_cache()

    payload = {
        "message": "Ping?",
        "channel": "email",
        "tone": "professional",
    }
    response = client.post("/v1/reply/draft", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key."


def test_auth_skipped_when_api_key_not_set(monkeypatch, client):
    monkeypatch.delenv("SMART_REPLY_API_KEY", raising=False)
    reset_settings_cache()

    payload = {
        "message": "Ping?",
        "channel": "email",
        "tone": "professional",
    }
    response = client.post("/v1/reply/draft", json=payload)
    assert response.status_code == 200
    assert len(response.json()["drafts"]) == 3


def test_rate_limit_returns_429(monkeypatch):
    # Tighten limit to 1 request/min for test predictability.
    monkeypatch.setenv("SMART_REPLY_RATE_LIMIT_PER_MINUTE", "1")
    reset_settings_cache()
    reset_rate_limit_cache()
    local_client = TestClient(create_app())

    payload = {"message": "Ping?", "channel": "email", "tone": "professional"}
    first = local_client.post("/v1/reply/draft", json=payload)
    assert first.status_code == 200

    second = local_client.post("/v1/reply/draft", json=payload)
    assert second.status_code == 429
    assert second.json()["detail"] == "Rate limit exceeded."
