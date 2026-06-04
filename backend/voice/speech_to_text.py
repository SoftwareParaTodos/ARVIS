from pathlib import Path
from typing import Any

from assistant.settings import get_settings
from voice.audio_utils import ALLOWED_AUDIO_EXTENSIONS


def is_stt_available() -> dict[str, Any]:
    settings = get_settings()
    if not settings["voice_enabled"] or not settings["stt_enabled"]:
        return {
            "available": False,
            "engine": settings["stt_engine"],
            "model": settings["stt_model"],
            "language": settings["stt_language"],
            "error": "STT desactivado en configuracion.",
        }

    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        return {
            "available": False,
            "engine": settings["stt_engine"],
            "model": settings["stt_model"],
            "language": settings["stt_language"],
            "error": "faster-whisper no esta instalado.",
        }

    return {
        "available": True,
        "engine": settings["stt_engine"],
        "model": settings["stt_model"],
        "language": settings["stt_language"],
        "error": None,
    }


def transcribe_audio_file(file_path: str) -> dict[str, Any]:
    settings = get_settings()
    base_response = {
        "available": False,
        "engine": settings["stt_engine"],
        "model": settings["stt_model"],
        "language": settings["stt_language"],
        "text": None,
        "segments": [],
        "error": None,
    }

    if not settings["voice_enabled"] or not settings["stt_enabled"]:
        return {**base_response, "error": "STT desactivado en configuracion."}

    audio_path = Path(file_path)
    if not audio_path.exists() or not audio_path.is_file():
        return {**base_response, "error": "El archivo de audio no existe."}

    if audio_path.suffix.lower() not in ALLOWED_AUDIO_EXTENSIONS:
        return {**base_response, "error": "Extension de audio no permitida."}

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return {**base_response, "error": "faster-whisper no esta instalado."}

    try:
        model = WhisperModel(
            settings["stt_model"],
            device=settings["stt_device"],
            compute_type=settings["stt_compute_type"],
        )
        segments, _info = model.transcribe(
            str(audio_path),
            language=settings["stt_language"],
        )
        segment_items = [
            {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
            }
            for segment in segments
        ]
        text = " ".join(item["text"] for item in segment_items).strip()

        return {
            **base_response,
            "available": True,
            "text": text or None,
            "segments": segment_items,
            "error": None,
        }
    except Exception as error:
        return {
            **base_response,
            "error": f"No se pudo transcribir el audio: {error}",
        }
