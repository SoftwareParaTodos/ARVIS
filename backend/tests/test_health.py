from main import health


def test_health_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(
        "main.get_ollama_status",
        lambda timeout_seconds=0.3: {
            "enabled": True,
            "available": False,
            "base_url": "http://127.0.0.1:11434",
            "model": "llama3.2",
            "timeout_seconds": 30,
            "error": "test",
        },
    )

    data = health()

    assert data["status"] == "OK"
    assert data["app"] == "ARVIS"
    assert data["version"] == "0.4.4"
    assert data["backend"] == "running"
    assert "storage_path" in data
    assert "database_exists" in data
    assert "settings_exists" in data
    assert "pending_actions_count" in data
    assert data["ai_enabled"] is True
    assert data["ai_available"] is False
    assert data["ai_model"] == "llama3.2"
    assert "voice_enabled" in data
    assert "stt_available" in data
    assert "tts_available" in data
    assert "mic_enabled" in data
    assert "mic_available" in data
