import requests

from assistant import local_ai


def test_local_ai_unavailable_does_not_break(monkeypatch) -> None:
    monkeypatch.setattr(
        local_ai,
        "get_settings",
        lambda: {
            "ollama_enabled": True,
            "ollama_base_url": "http://127.0.0.1:11434",
            "ollama_model": "llama3.2",
            "ollama_timeout_seconds": 30,
            "conversation_history_enabled": True,
            "conversation_history_limit": 6,
        },
    )

    def raise_connection_error(*args, **kwargs):
        raise requests.ConnectionError("ollama unavailable")

    monkeypatch.setattr(local_ai.requests, "post", raise_connection_error)

    response = local_ai.ask_ollama("hola")

    assert response["available"] is False
    assert response["model"] == "llama3.2"
    assert response["response"] is None
    assert "ollama unavailable" in response["error"]


def test_ollama_status_unavailable_does_not_break(monkeypatch) -> None:
    monkeypatch.setattr(
        local_ai,
        "get_settings",
        lambda: {
            "ollama_enabled": True,
            "ollama_base_url": "http://127.0.0.1:11434",
            "ollama_model": "llama3.2",
            "ollama_timeout_seconds": 30,
            "conversation_history_enabled": True,
            "conversation_history_limit": 6,
        },
    )

    def raise_connection_error(*args, **kwargs):
        raise requests.ConnectionError("ollama unavailable")

    monkeypatch.setattr(local_ai.requests, "get", raise_connection_error)

    status = local_ai.get_ollama_status()

    assert status["enabled"] is True
    assert status["available"] is False
    assert status["base_url"] == "http://127.0.0.1:11434"
    assert status["model"] == "llama3.2"
    assert status["timeout_seconds"] == 30
    assert "ollama unavailable" in status["error"]


def test_ollama_models_unavailable_does_not_break(monkeypatch) -> None:
    monkeypatch.setattr(
        local_ai,
        "get_settings",
        lambda: {
            "ollama_enabled": True,
            "ollama_base_url": "http://127.0.0.1:11434",
            "ollama_model": "llama3.2",
            "ollama_timeout_seconds": 30,
            "conversation_history_enabled": True,
            "conversation_history_limit": 6,
        },
    )

    def raise_connection_error(*args, **kwargs):
        raise requests.ConnectionError("ollama unavailable")

    monkeypatch.setattr(local_ai.requests, "get", raise_connection_error)

    response = local_ai.get_ollama_models()

    assert response["available"] is False
    assert response["current_model"] == "llama3.2"
    assert response["models"] == []
    assert "ollama unavailable" in response["error"]
