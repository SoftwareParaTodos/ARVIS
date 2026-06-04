import builtins
from io import BytesIO

from api.routes_voice import voice_status
from voice import speech_to_text, text_to_speech, voice_service
from voice.audio_utils import validate_audio_extension


def test_voice_status_responds_without_voice_dependencies(monkeypatch) -> None:
    monkeypatch.setattr(
        "api.routes_voice.get_voice_status",
        lambda: {
            "voice_enabled": True,
            "stt": {"available": False, "error": "missing"},
            "tts": {"available": False, "error": "missing"},
            "storage_path": "C:\\ARVIS\\backend\\storage\\voice",
        },
    )

    response = voice_status()

    assert response["voice_enabled"] is True
    assert response["stt"]["available"] is False
    assert response["tts"]["available"] is False


def test_stt_missing_dependency_returns_controlled_error(monkeypatch) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "faster_whisper":
            raise ImportError("missing faster-whisper")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    response = speech_to_text.is_stt_available()

    assert response["available"] is False
    assert "faster-whisper" in response["error"]


def test_tts_missing_dependency_returns_controlled_error(monkeypatch) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pyttsx3":
            raise ImportError("missing pyttsx3")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    response = text_to_speech.is_tts_available()

    assert response["available"] is False
    assert "pyttsx3" in response["error"]


def test_validate_audio_extension_accepts_common_formats() -> None:
    assert validate_audio_extension("audio.wav") is True
    assert validate_audio_extension("audio.mp3") is True
    assert validate_audio_extension("audio.webm") is True


def test_validate_audio_extension_rejects_dangerous_extension() -> None:
    assert validate_audio_extension("payload.exe") is False
    assert validate_audio_extension("../payload.bat") is False


def test_voice_service_uses_brain_for_transcribed_text(monkeypatch, tmp_path) -> None:
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"fake")

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

    response = voice_service.process_voice_chat(str(audio_path))

    assert response["status"] == "response"
    assert response["transcribed_text"] == "ayuda"
    assert response["assistant_response"]["message"] == "brain recibio: ayuda"


def test_transcribe_uploaded_audio_rejects_bad_extension() -> None:
    response = voice_service.transcribe_uploaded_audio(BytesIO(b"fake"), "bad.exe")

    assert response["saved_path"] is None
    assert response["transcription"]["available"] is False
