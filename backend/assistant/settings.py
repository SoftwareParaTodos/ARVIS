import json
from copy import deepcopy
from typing import Any

from config import (
    CONVERSATION_HISTORY_ENABLED,
    CONVERSATION_HISTORY_LIMIT,
    MIC_CHANNELS,
    MIC_DEFAULT_RECORD_SECONDS,
    MIC_ENABLED,
    MIC_ENGINE,
    MIC_INPUT_DEVICE,
    MIC_MAX_RECORD_SECONDS,
    MIC_SAMPLE_RATE,
    MIC_SAVE_RECORDINGS,
    OLLAMA_BASE_URL,
    OLLAMA_ENABLED,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
    PENDING_ACTION_EXPIRATION_MINUTES,
    SETTINGS_PATH,
    STORAGE_DIR,
    STT_COMPUTE_TYPE,
    STT_DEVICE,
    STT_ENABLED,
    STT_ENGINE,
    STT_LANGUAGE,
    STT_MODEL,
    TTS_ENABLED,
    TTS_ENGINE,
    TTS_RATE,
    TTS_VOICE,
    TTS_VOLUME,
    VOICE_ENABLED,
    VOICE_OUTPUT_FORMAT,
    VOICE_STORAGE_KEEP_FILES,
)


DEFAULT_SETTINGS: dict[str, Any] = {
    "ollama_enabled": OLLAMA_ENABLED,
    "ollama_base_url": OLLAMA_BASE_URL,
    "ollama_model": OLLAMA_MODEL,
    "ollama_timeout_seconds": OLLAMA_TIMEOUT_SECONDS,
    "conversation_history_enabled": CONVERSATION_HISTORY_ENABLED,
    "conversation_history_limit": CONVERSATION_HISTORY_LIMIT,
    "pending_action_expiration_minutes": PENDING_ACTION_EXPIRATION_MINUTES,
    "voice_enabled": VOICE_ENABLED,
    "stt_enabled": STT_ENABLED,
    "stt_engine": STT_ENGINE,
    "stt_model": STT_MODEL,
    "stt_language": STT_LANGUAGE,
    "stt_device": STT_DEVICE,
    "stt_compute_type": STT_COMPUTE_TYPE,
    "tts_enabled": TTS_ENABLED,
    "tts_engine": TTS_ENGINE,
    "tts_voice": TTS_VOICE,
    "tts_rate": TTS_RATE,
    "tts_volume": TTS_VOLUME,
    "voice_output_format": VOICE_OUTPUT_FORMAT,
    "voice_storage_keep_files": VOICE_STORAGE_KEEP_FILES,
    "mic_enabled": MIC_ENABLED,
    "mic_engine": MIC_ENGINE,
    "mic_sample_rate": MIC_SAMPLE_RATE,
    "mic_channels": MIC_CHANNELS,
    "mic_max_record_seconds": MIC_MAX_RECORD_SECONDS,
    "mic_default_record_seconds": MIC_DEFAULT_RECORD_SECONDS,
    "mic_input_device": MIC_INPUT_DEVICE,
    "mic_save_recordings": MIC_SAVE_RECORDINGS,
}


def _write_settings(settings: dict[str, Any]) -> dict[str, Any]:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(settings, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return deepcopy(settings)


def _validate_settings(data: dict[str, Any]) -> dict[str, Any]:
    settings = deepcopy(DEFAULT_SETTINGS)

    if isinstance(data.get("ollama_enabled"), bool):
        settings["ollama_enabled"] = data["ollama_enabled"]

    if isinstance(data.get("ollama_base_url"), str) and data["ollama_base_url"].strip():
        settings["ollama_base_url"] = data["ollama_base_url"].strip().rstrip("/")

    if isinstance(data.get("ollama_model"), str) and data["ollama_model"].strip():
        settings["ollama_model"] = data["ollama_model"].strip()

    timeout = data.get("ollama_timeout_seconds")
    if isinstance(timeout, int) and not isinstance(timeout, bool) and 3 <= timeout <= 180:
        settings["ollama_timeout_seconds"] = timeout

    if isinstance(data.get("conversation_history_enabled"), bool):
        settings["conversation_history_enabled"] = data["conversation_history_enabled"]

    history_limit = data.get("conversation_history_limit")
    if (
        isinstance(history_limit, int)
        and not isinstance(history_limit, bool)
        and 0 <= history_limit <= 20
    ):
        settings["conversation_history_limit"] = history_limit

    pending_expiration = data.get("pending_action_expiration_minutes")
    if (
        isinstance(pending_expiration, int)
        and not isinstance(pending_expiration, bool)
        and 1 <= pending_expiration <= 1440
    ):
        settings["pending_action_expiration_minutes"] = pending_expiration

    if isinstance(data.get("voice_enabled"), bool):
        settings["voice_enabled"] = data["voice_enabled"]

    if isinstance(data.get("stt_enabled"), bool):
        settings["stt_enabled"] = data["stt_enabled"]

    if data.get("stt_engine") == "faster_whisper":
        settings["stt_engine"] = data["stt_engine"]

    if data.get("stt_model") in {"tiny", "base", "small", "medium", "large-v3"}:
        settings["stt_model"] = data["stt_model"]

    if isinstance(data.get("stt_language"), str) and data["stt_language"].strip():
        settings["stt_language"] = data["stt_language"].strip()

    if data.get("stt_device") in {"cpu", "cuda", "auto"}:
        settings["stt_device"] = data["stt_device"]

    if isinstance(data.get("stt_compute_type"), str) and data["stt_compute_type"].strip():
        settings["stt_compute_type"] = data["stt_compute_type"].strip()

    if isinstance(data.get("tts_enabled"), bool):
        settings["tts_enabled"] = data["tts_enabled"]

    if data.get("tts_engine") == "pyttsx3":
        settings["tts_engine"] = data["tts_engine"]

    if isinstance(data.get("tts_voice"), str) and data["tts_voice"].strip():
        settings["tts_voice"] = data["tts_voice"].strip()

    tts_rate = data.get("tts_rate")
    if isinstance(tts_rate, int) and not isinstance(tts_rate, bool) and 80 <= tts_rate <= 260:
        settings["tts_rate"] = tts_rate

    tts_volume = data.get("tts_volume")
    if (
        isinstance(tts_volume, (int, float))
        and not isinstance(tts_volume, bool)
        and 0.0 <= float(tts_volume) <= 1.0
    ):
        settings["tts_volume"] = float(tts_volume)

    if data.get("voice_output_format") == "wav":
        settings["voice_output_format"] = data["voice_output_format"]

    if isinstance(data.get("voice_storage_keep_files"), bool):
        settings["voice_storage_keep_files"] = data["voice_storage_keep_files"]

    if isinstance(data.get("mic_enabled"), bool):
        settings["mic_enabled"] = data["mic_enabled"]

    if data.get("mic_engine") == "sounddevice":
        settings["mic_engine"] = data["mic_engine"]

    if data.get("mic_sample_rate") in {8000, 16000, 22050, 44100, 48000}:
        settings["mic_sample_rate"] = data["mic_sample_rate"]

    if data.get("mic_channels") in {1, 2}:
        settings["mic_channels"] = data["mic_channels"]

    mic_max = data.get("mic_max_record_seconds")
    if isinstance(mic_max, int) and not isinstance(mic_max, bool) and 1 <= mic_max <= 60:
        settings["mic_max_record_seconds"] = mic_max

    mic_default = data.get("mic_default_record_seconds")
    if (
        isinstance(mic_default, int)
        and not isinstance(mic_default, bool)
        and 1 <= mic_default <= settings["mic_max_record_seconds"]
    ):
        settings["mic_default_record_seconds"] = mic_default

    mic_input_device = data.get("mic_input_device")
    if mic_input_device is None or isinstance(mic_input_device, (str, int)):
        settings["mic_input_device"] = mic_input_device

    if isinstance(data.get("mic_save_recordings"), bool):
        settings["mic_save_recordings"] = data["mic_save_recordings"]

    return settings


def get_settings() -> dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return _write_settings(DEFAULT_SETTINGS)

    try:
        loaded = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _write_settings(DEFAULT_SETTINGS)

    if not isinstance(loaded, dict):
        return _write_settings(DEFAULT_SETTINGS)

    validated = _validate_settings(loaded)
    if validated != loaded:
        return _write_settings(validated)

    return deepcopy(validated)


def update_settings(data: dict[str, Any]) -> dict[str, Any]:
    current = get_settings()
    merged = {**current, **data}
    validated = _validate_settings(merged)
    return _write_settings(validated)


def reset_settings() -> dict[str, Any]:
    return _write_settings(DEFAULT_SETTINGS)


def get_current_ai_model() -> str:
    return str(get_settings()["ollama_model"])
