from datetime import datetime
from pathlib import Path
from typing import Any

from assistant.settings import get_settings
from voice.audio_utils import VOICE_TTS_DIR, ensure_voice_storage


MAX_TTS_TEXT_LENGTH = 4000


def is_tts_available() -> dict[str, Any]:
    settings = get_settings()
    if not settings["voice_enabled"] or not settings["tts_enabled"]:
        return {
            "available": False,
            "engine": settings["tts_engine"],
            "error": "TTS desactivado en configuracion.",
        }

    try:
        import pyttsx3  # noqa: F401
    except ImportError:
        return {
            "available": False,
            "engine": settings["tts_engine"],
            "error": "pyttsx3 no esta instalado.",
        }

    return {
        "available": True,
        "engine": settings["tts_engine"],
        "error": None,
    }


def synthesize_to_file(text: str, output_path: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    base_response = {
        "available": False,
        "engine": settings["tts_engine"],
        "output_path": None,
        "spoken": False,
        "error": None,
    }

    if not settings["voice_enabled"] or not settings["tts_enabled"]:
        return {**base_response, "error": "TTS desactivado en configuracion."}

    clean_text = text.strip()
    if not clean_text:
        return {**base_response, "error": "No hay texto para sintetizar."}

    if len(clean_text) > MAX_TTS_TEXT_LENGTH:
        clean_text = clean_text[:MAX_TTS_TEXT_LENGTH]

    try:
        import pyttsx3
    except ImportError:
        return {**base_response, "error": "pyttsx3 no esta instalado."}

    ensure_voice_storage()
    target_path = Path(output_path) if output_path else _default_tts_path()
    if target_path.suffix.lower() != ".wav":
        target_path = target_path.with_suffix(".wav")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", settings["tts_rate"])
        engine.setProperty("volume", settings["tts_volume"])
        engine.save_to_file(clean_text, str(target_path))
        engine.runAndWait()

        return {
            **base_response,
            "available": True,
            "output_path": str(target_path),
            "spoken": False,
            "error": None,
        }
    except Exception as error:
        return {
            **base_response,
            "error": f"No se pudo generar audio TTS: {error}",
        }


def speak_text(text: str) -> dict[str, Any]:
    settings = get_settings()
    base_response = {
        "available": False,
        "engine": settings["tts_engine"],
        "output_path": None,
        "spoken": False,
        "error": None,
    }

    if not settings["voice_enabled"] or not settings["tts_enabled"]:
        return {**base_response, "error": "TTS desactivado en configuracion."}

    clean_text = text.strip()
    if not clean_text:
        return {**base_response, "error": "No hay texto para leer."}

    if len(clean_text) > MAX_TTS_TEXT_LENGTH:
        clean_text = clean_text[:MAX_TTS_TEXT_LENGTH]

    try:
        import pyttsx3
    except ImportError:
        return {**base_response, "error": "pyttsx3 no esta instalado."}

    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", settings["tts_rate"])
        engine.setProperty("volume", settings["tts_volume"])
        engine.say(clean_text)
        engine.runAndWait()

        return {
            **base_response,
            "available": True,
            "spoken": True,
            "error": None,
        }
    except Exception as error:
        return {
            **base_response,
            "error": f"No se pudo reproducir TTS: {error}",
        }


def _default_tts_path() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return VOICE_TTS_DIR / f"{timestamp}-tts.wav"
