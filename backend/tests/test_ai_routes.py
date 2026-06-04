from api.routes_ai import ModelRequest, ai_model, ai_models, ai_status


def test_ai_status_route(monkeypatch) -> None:
    monkeypatch.setattr(
        "api.routes_ai.get_ollama_status",
        lambda: {
            "enabled": True,
            "available": False,
            "base_url": "http://127.0.0.1:11434",
            "model": "llama3.2",
            "timeout_seconds": 30,
            "error": "test",
        },
    )

    response = ai_status()

    assert response["enabled"] is True
    assert response["available"] is False
    assert response["base_url"] == "http://127.0.0.1:11434"
    assert response["model"] == "llama3.2"
    assert response["timeout_seconds"] == 30
    assert response["error"] == "test"


def test_ai_models_route_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        "api.routes_ai.get_ollama_models",
        lambda: {
            "available": False,
            "current_model": "llama3.2",
            "models": [],
            "error": "ollama unavailable",
        },
    )

    response = ai_models()

    assert response["available"] is False
    assert response["models"] == []
    assert response["error"] == "ollama unavailable"


def test_ai_model_route_saves_even_without_verification(monkeypatch) -> None:
    monkeypatch.setattr(
        "api.routes_ai.set_ollama_model",
        lambda model: {
            "settings": {"ollama_model": model},
            "ai_status": {"available": False},
            "details": {"warning": "not verified"},
        },
    )

    response = ai_model(ModelRequest(model="qwen2.5"))

    assert response["settings"]["ollama_model"] == "qwen2.5"
    assert response["details"]["warning"] == "not verified"
