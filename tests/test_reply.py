import json
import sys
import types

from fastapi.testclient import TestClient
import pytest

from app.main import create_app
from app.core.config import reset_settings_cache
from app.middleware.rate_limit import reset_rate_limit_cache
from app.api.schemas import DraftRequest
from app.services.prompts import build_user_prompt, SYSTEM_PROMPT
from app.services.llm import generate_reply_drafts


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
        "incoming_message": "Can you share the latest metrics for Q1?",
        "channel": "email",
        "tone": "professional",
    }
    response = client.post("/v1/reply/draft", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["drafts"]) == 3
    assert data["channel_applied"] == "email"
    assert data["request_id"] != "stub"
    assert len(data["request_id"]) == 8


def test_auth_required_when_api_key_configured(monkeypatch, client):
    monkeypatch.setenv("SMART_REPLY_API_KEY", "secret")
    reset_settings_cache()

    payload = {
        "incoming_message": "Ping?",
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
        "incoming_message": "Ping?",
        "channel": "email",
        "tone": "professional",
    }
    response = client.post("/v1/reply/draft", json=payload)
    assert response.status_code == 200
    assert len(response.json()["drafts"]) == 3


def test_auth_succeeds_with_valid_key(monkeypatch):
    monkeypatch.setenv("SMART_REPLY_API_KEY", "secret")
    reset_settings_cache()
    reset_rate_limit_cache()
    authed_client = TestClient(create_app())

    payload = {"incoming_message": "Hi", "channel": "email", "tone": "professional"}
    response = authed_client.post("/v1/reply/draft", json=payload, headers={"x-api-key": "secret"})
    assert response.status_code == 200


def test_rate_limit_returns_429(monkeypatch):
    # Tighten limit to 1 request/min for test predictability.
    monkeypatch.setenv("SMART_REPLY_RATE_LIMIT_PER_MINUTE", "1")
    reset_settings_cache()
    reset_rate_limit_cache()
    local_client = TestClient(create_app())

    payload = {"incoming_message": "Ping?", "channel": "email", "tone": "professional"}
    first = local_client.post("/v1/reply/draft", json=payload)
    assert first.status_code == 200

    second = local_client.post("/v1/reply/draft", json=payload)
    assert second.status_code == 429
    assert second.json()["detail"] == "Rate limit exceeded."


def test_schema_validation_rejects_bad_tone(client):
    payload = {"incoming_message": "Hi", "channel": "email", "tone": "not-a-tone"}
    response = client.post("/v1/reply/draft", json=payload)
    assert response.status_code == 422


def test_build_user_prompt_is_deterministic():
    request = DraftRequest(
        incoming_message="Hello there",
        context="Thread with ops",
        channel="email",
        tone="friendly",
        constraints={"max_words": 50, "must_include_question": True, "avoid_phrases": ["ASAP", "FYI"]},
    )
    prompt = build_user_prompt(request)

    expected_snippet = (
        "Generate reply drafts for the following input.\n"
        "- channel: email\n"
        "- tone: friendly\n"
        "- language: UK English (default)\n"
        "- message: Hello there\n"
        "- context: Thread with ops\n"
        "- constraints:\n"
        "- max_words: 50\n"
        "- must_include_question: true\n"
        "- avoid_phrases: ['ASAP', 'FYI']"
    )
    assert expected_snippet in prompt
    # ensure schema block is present
    assert '"drafts": [' in prompt
    assert "- Return JSON only." in prompt


def test_generate_reply_drafts_uses_openai_and_returns_valid(monkeypatch):
    # Force OpenAI path
    monkeypatch.setenv("SMART_REPLY_OPENAI_API_KEY", "test-key")
    reset_settings_cache()

    captured: dict = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)

            class Resp:
                id = "resp_123"
                output_text = json.dumps(
                    {
                        "request_id": "resp_123",
                        "detected_tone": "professional",
                        "channel_applied": "email",
                        "drafts": [
                            {"label": "Option 1", "text": "Draft one"},
                            {"label": "Option 2", "text": "Draft two"},
                            {"label": "Option 3", "text": "Draft three"},
                        ],
                        "notes": "unit-test",
                        "confidence_score": 0.9,
                    }
                )

            return Resp()

    class FakeOpenAI:
        def __init__(self, api_key, base_url=None):
            captured["init"] = {"api_key": api_key, "base_url": base_url}
            self.responses = FakeResponses()

    fake_module = types.SimpleNamespace(OpenAI=FakeOpenAI)
    monkeypatch.setitem(sys.modules, "openai", fake_module)

    request = DraftRequest(incoming_message="Test msg", channel="email", tone="professional")
    result = generate_reply_drafts(request)

    assert result.drafts[0].text == "Draft one"
    # Ensure client was initialized with our API key
    assert captured["init"]["api_key"] == "test-key"
    # Ensure system prompt is sent first
    assert captured["input"][0]["content"] == SYSTEM_PROMPT
    assert captured["response_format"]["type"] == "json_object"
