from assistant import settings


def test_get_settings_creates_file(tmp_path, monkeypatch) -> None:
    settings_path = tmp_path / "settings.json"
    monkeypatch.setattr(settings, "SETTINGS_PATH", settings_path)

    current = settings.get_settings()

    assert settings_path.exists()
    assert current["ollama_enabled"] is True
    assert current["ollama_model"] == "llama3.2"
    assert current["pending_action_expiration_minutes"] == 10
    assert current["voice_enabled"] is True
    assert current["stt_model"] == "base"
    assert current["tts_rate"] == 175
    assert current["mic_enabled"] is True
    assert current["mic_sample_rate"] == 16000
    assert current["mic_default_record_seconds"] == 5


def test_update_settings_changes_only_allowed_keys(tmp_path, monkeypatch) -> None:
    settings_path = tmp_path / "settings.json"
    monkeypatch.setattr(settings, "SETTINGS_PATH", settings_path)
    settings.reset_settings()

    updated = settings.update_settings(
        {
            "ollama_model": "qwen2.5",
            "unknown_key": "ignored",
            "conversation_history_limit": 12,
        }
    )

    assert updated["ollama_model"] == "qwen2.5"
    assert updated["conversation_history_limit"] == 12
    assert "unknown_key" not in updated


def test_invalid_timeout_does_not_break(tmp_path, monkeypatch) -> None:
    settings_path = tmp_path / "settings.json"
    monkeypatch.setattr(settings, "SETTINGS_PATH", settings_path)
    settings.reset_settings()

    updated = settings.update_settings({"ollama_timeout_seconds": 1})

    assert updated["ollama_timeout_seconds"] == 30


def test_invalid_pending_expiration_does_not_break(tmp_path, monkeypatch) -> None:
    settings_path = tmp_path / "settings.json"
    monkeypatch.setattr(settings, "SETTINGS_PATH", settings_path)
    settings.reset_settings()

    updated = settings.update_settings({"pending_action_expiration_minutes": 0})

    assert updated["pending_action_expiration_minutes"] == 10


def test_voice_settings_complete_missing_keys(tmp_path, monkeypatch) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text('{"ollama_model": "qwen2.5"}\n', encoding="utf-8")
    monkeypatch.setattr(settings, "SETTINGS_PATH", settings_path)

    current = settings.get_settings()

    assert current["ollama_model"] == "qwen2.5"
    assert current["voice_enabled"] is True
    assert current["stt_model"] == "base"
    assert current["tts_volume"] == 1.0
    assert current["mic_enabled"] is True
    assert current["mic_channels"] == 1


def test_invalid_voice_values_do_not_break(tmp_path, monkeypatch) -> None:
    settings_path = tmp_path / "settings.json"
    monkeypatch.setattr(settings, "SETTINGS_PATH", settings_path)
    settings.reset_settings()

    updated = settings.update_settings(
        {
            "stt_model": "giant",
            "tts_rate": 20,
            "tts_volume": 2.0,
        }
    )

    assert updated["stt_model"] == "base"
    assert updated["tts_rate"] == 175
    assert updated["tts_volume"] == 1.0


def test_invalid_microphone_values_do_not_break(tmp_path, monkeypatch) -> None:
    settings_path = tmp_path / "settings.json"
    monkeypatch.setattr(settings, "SETTINGS_PATH", settings_path)
    settings.reset_settings()

    updated = settings.update_settings(
        {
            "mic_sample_rate": 123,
            "mic_channels": 9,
            "mic_max_record_seconds": 100,
            "mic_default_record_seconds": 99,
        }
    )

    assert updated["mic_sample_rate"] == 16000
    assert updated["mic_channels"] == 1
    assert updated["mic_max_record_seconds"] == 30
    assert updated["mic_default_record_seconds"] == 5
