from assistant.brain import handle_message


def test_brain_system_info() -> None:
    response = handle_message("info del sistema")

    assert response["status"] == "executed"
    assert response["intent"] == "system_info"
    assert response["tool"] == "system_info"
    assert response["risk_level"] == "safe"
    assert response["requires_confirmation"] is False
    assert "python_version" in response["details"]


def test_brain_fallback_when_ollama_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        "assistant.brain.ask_ollama",
        lambda message, system_prompt=None, conversation_context=None: {
            "available": False,
            "model": "llama3.2",
            "response": None,
            "error": "connection refused",
        },
    )

    response = handle_message("hola arvis")

    assert response["status"] == "response"
    assert response["intent"] == "chat"
    assert response["tool"] is None
    assert response["risk_level"] == "safe"
    assert "Todavia no tengo IA local disponible" in response["message"]


def test_brain_help_does_not_need_ollama(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Ollama should not be called for help")

    monkeypatch.setattr("assistant.brain.ask_ollama", fail_if_called)

    response = handle_message("ayuda")

    assert response["status"] == "response"
    assert response["intent"] == "help"
    assert response["tool"] is None
    assert "abrir calculadora" in response["message"]


def test_brain_blocks_dangerous_file_action(monkeypatch) -> None:
    monkeypatch.setattr(
        "assistant.brain.create_pending_action",
        lambda **kwargs: {
            "id": 123,
            "created_at": "2026-01-01T00:00:00+00:00",
            "original_message": kwargs["original_message"],
            "detected_intent": kwargs["detected_intent"],
            "requested_tool": kwargs["requested_tool"],
            "parameters": kwargs["parameters"],
            "risk_level": kwargs["risk_level"],
            "status": "pending",
            "resolved_at": None,
        },
    )

    response = handle_message("borrar archivos")

    assert response["status"] == "confirmation_required"
    assert response["risk_level"] == "confirmation_required"
    assert response["requires_confirmation"] is True
    assert response["details"]["pending_action"]["id"] == 123


def test_confirm_without_pending_actions(monkeypatch) -> None:
    monkeypatch.setattr("assistant.brain.expire_old_pending_actions", lambda: 0)
    monkeypatch.setattr("assistant.brain.list_pending_actions", lambda limit=2: [])

    response = handle_message("confirmo")

    assert response["status"] == "response"
    assert "No hay acciones pendientes" in response["message"]


def test_cancel_without_pending_actions(monkeypatch) -> None:
    monkeypatch.setattr("assistant.brain.expire_old_pending_actions", lambda: 0)
    monkeypatch.setattr("assistant.brain.list_pending_actions", lambda limit=2: [])

    response = handle_message("cancelar")

    assert response["status"] == "response"
    assert "No hay acciones pendientes" in response["message"]
