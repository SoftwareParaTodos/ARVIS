import builtins

from api.routes_voice import voice_mic_status
from voice import microphone_capture, voice_service
from voice.audio_utils import normalize_record_seconds


def test_microphone_status_responds_without_dependency(monkeypatch) -> None:
    monkeypatch.setattr(
        "api.routes_voice.get_microphone_status",
        lambda: {
            "mic_enabled": True,
            "enabled": True,
            "available": False,
            "engine": "sounddevice",
            "sample_rate": 16000,
            "channels": 1,
            "default_record_seconds": 5,
            "max_record_seconds": 30,
            "error": "missing",
        },
    )

    response = voice_mic_status()

    assert response["mic_enabled"] is True
    assert response["available"] is False


def test_microphone_devices_missing_dependency_controlled_error(monkeypatch) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "sounddevice":
            raise ImportError("missing sounddevice")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    response = microphone_capture.list_input_devices()

    assert response["available"] is False
    assert response["devices"] == []
    assert "sounddevice" in response["error"]


def test_invalid_duration_is_normalized() -> None:
    assert normalize_record_seconds(None, 5, 30) == 5
    assert normalize_record_seconds(100, 5, 30) == 30
    assert normalize_record_seconds(-1, 5, 30) == 1


def test_mic_disabled_prevents_recording(monkeypatch) -> None:
    monkeypatch.setattr(
        microphone_capture,
        "get_settings",
        lambda: {
            "mic_enabled": False,
            "mic_engine": "sounddevice",
            "mic_sample_rate": 16000,
            "mic_channels": 1,
            "mic_max_record_seconds": 30,
            "mic_default_record_seconds": 5,
            "mic_input_device": None,
            "mic_save_recordings": True,
        },
    )

    response = microphone_capture.record_microphone_to_file()

    assert response["success"] is False
    assert "desactivado" in response["error"]


def test_process_microphone_chat_uses_brain_only_after_transcription(monkeypatch) -> None:
    monkeypatch.setattr(
        voice_service,
        "record_from_microphone",
        lambda duration_seconds=None: {
            "success": True,
            "engine": "sounddevice",
            "duration_seconds": 3,
            "sample_rate": 16000,
            "channels": 1,
            "output_path": "C:\\ARVIS\\backend\\storage\\voice\\input\\test.wav",
            "error": None,
        },
    )
    monkeypatch.setattr(
        voice_service,
        "transcribe_audio_file",
        lambda path: {
            "available": True,
            "engine": "faster_whisper",
            "model": "base",
            "language": "es",
            "text": "ayuda",
            "segments": [],
            "error": None,
        },
    )
    monkeypatch.setattr(
        voice_service,
        "handle_message",
        lambda message: {
            "status": "response",
            "message": f"brain recibio: {message}",
            "intent": "help",
            "tool": None,
            "requires_confirmation": False,
            "risk_level": "safe",
            "details": {},
        },
    )
    monkeypatch.setattr(voice_service, "_delete_recording_if_configured", lambda path: None)

    response = voice_service.process_microphone_chat(duration_seconds=3)

    assert response["status"] == "response"
    assert response["recorded_audio_path"].endswith("test.wav")
    assert response["transcribed_text"] == "ayuda"
    assert response["assistant_response"]["message"] == "brain recibio: ayuda"
