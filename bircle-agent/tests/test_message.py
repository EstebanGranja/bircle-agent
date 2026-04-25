"""Tests del endpoint /message para los 3 proveedores LLM"""

import pytest
from fastapi.testclient import TestClient
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from app.api.dependencies import get_agent_service
from app.core.config import Settings, settings
from app.llm.provider import get_llm
from app.schemas.classification import ClassificationOutput
from app.schemas.message import MessageResponse
from main import app


_FAKE_RESPONSE = MessageResponse(
    reply="Claro, te puedo ayudar con la información del producto.",
    classification=ClassificationOutput(
        category="sales",
        priority="medium",
        intent="ask_info",
        sentiment="neutral",
        requires_human_escalation=False,
        reasoning="El usuario está consultando información comercial.",
        confidence_score=0.9,
    ),
)


class _FakeAgentService:
    """AgentService de prueba que devuelve _FAKE_RESPONSE sin llamar al LLM"""

    async def process_turn(self, session_id: str, user_message: str) -> MessageResponse:
        return _FAKE_RESPONSE


@pytest.mark.parametrize(
    "provider, model, api_key, expected_cls",
    [
        ("ollama", "llama3.2:3b", None, ChatOllama),
        ("openai", "gpt-4o-mini", "sk-test-fake", ChatOpenAI),
        ("anthropic", "claude-haiku-4-5-20251001", "sk-ant-test-fake", ChatAnthropic),
    ],
)
def test_get_llm_builds_correct_provider(monkeypatch, provider, model, api_key, expected_cls):
    """get_llm() instancia el cliente correcto para cada proveedor"""
    monkeypatch.setattr(settings, "llm_provider", provider)
    monkeypatch.setattr(settings, "llm_model_name", model)
    monkeypatch.setattr(settings, "llm_api_key", api_key)

    assert isinstance(get_llm(), expected_cls)


def test_get_llm_rejects_unknown_provider(monkeypatch):
    """get_llm() falla si el proveedor no es uno de los 3 soportados"""
    monkeypatch.setattr(settings, "llm_provider", "gemini")
    with pytest.raises(ValueError, match="Proveedor LLM no soportado"):
        get_llm()


def test_openai_provider_does_not_force_response_format(monkeypatch):
    """El provider de OpenAI no inyecta response_format (chocaría con with_structured_output)"""
    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "llm_model_name", "gpt-4o-mini")
    monkeypatch.setattr(settings, "llm_api_key", "sk-test-fake")

    llm = get_llm()
    assert "response_format" not in (getattr(llm, "model_kwargs", {}) or {})


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_settings_rejects_cloud_provider_without_api_key(provider, monkeypatch):
    """Los proveedores cloud fallan si falta LLM_API_KEY"""
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("LLM_MODEL_NAME", "test-model")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert "LLM_API_KEY" in str(exc_info.value)


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_settings_accepts_cloud_provider_with_api_key(provider, monkeypatch):
    """Los proveedores cloud cargan si LLM_API_KEY está presente"""
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("LLM_MODEL_NAME", "test-model")
    monkeypatch.setenv("LLM_API_KEY", "fake-key-123")

    s = Settings(_env_file=None)
    assert s.llm_provider == provider
    assert s.llm_api_key == "fake-key-123"


def test_settings_accepts_ollama_without_api_key(monkeypatch):
    """Ollama no exige api key"""
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_MODEL_NAME", "llama3.2:3b")

    s = Settings(_env_file=None)
    assert s.llm_provider == "ollama"
    assert s.llm_api_key is None


@pytest.fixture
def client_with_fake_agent():
    """TestClient con el AgentService reemplazado por un fake"""
    app.dependency_overrides[get_agent_service] = lambda: _FakeAgentService()
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "provider, model, api_key",
    [
        ("ollama", "llama3.2:3b", None),
        ("openai", "gpt-4o-mini", "sk-test-fake"),
        ("anthropic", "claude-haiku-4-5-20251001", "sk-ant-test-fake"),
    ],
)
def test_message_endpoint_returns_valid_response(
    monkeypatch, client_with_fake_agent, provider, model, api_key
):
    """POST /message responde 200 con shape válido para los 3 proveedores"""
    monkeypatch.setattr(settings, "llm_provider", provider)
    monkeypatch.setattr(settings, "llm_model_name", model)
    monkeypatch.setattr(settings, "llm_api_key", api_key)

    response = client_with_fake_agent.post(
        "/message",
        json={
            "session_id": "test-session-1",
            "message": "Hola, quería información sobre un producto",
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert isinstance(body.get("reply"), str) and body["reply"]

    cls = body["classification"]
    assert cls["category"] in {"billing", "support", "sales", "complaint", "general"}
    assert cls["priority"] in {"low", "medium", "high", "urgent"}
    assert cls["intent"] in {"ask_info", "complain", "request_action", "report_issue", "other"}
    assert cls["sentiment"] in {"positive", "neutral", "negative"}
    assert isinstance(cls["requires_human_escalation"], bool)
    assert 0.0 <= cls["confidence_score"] <= 1.0
    assert len(cls["reasoning"]) >= 10


def test_message_endpoint_rejects_invalid_session_id(client_with_fake_agent):
    """session_id con caracteres no permitidos → 422"""
    response = client_with_fake_agent.post(
        "/message",
        json={"session_id": "invalid session!", "message": "Hola"},
    )
    assert response.status_code == 422


def test_message_endpoint_rejects_empty_message(client_with_fake_agent):
    """message vacío → 422"""
    response = client_with_fake_agent.post(
        "/message",
        json={"session_id": "test-session-1", "message": ""},
    )
    assert response.status_code == 422
