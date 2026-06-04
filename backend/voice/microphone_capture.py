import wave
from pathlib import Path
from typing import Any

from assistant.settings import get_settings
from voice.audio_utils import build_voice_input_path, normalize_record_seconds, safe_wav_filename


def is_microphone_available() -> dict[str, Any]:
    settings = get_settings()
    if not settings["mic_enabled"]:
        return {
            "available": False,
            "engine": settings["mic_engine"],
            "error": "Microfono desactivado en configuracion.",
        }

    try:
        import sounddevice as sd  # noqa: F401
        import numpy as np  # noqa: F401
    except ImportError:
        return {
            "available": False,
            "engine": settings["mic_engine"],
            "error": "sounddevice o numpy no estan instalados.",
        }

    return {
        "available": True,
        "engine": settings["mic_engine"],
        "error": None,
    }


def list_input_devices() -> dict[str, Any]:
    settings = get_settings()
    if not settings["mic_enabled"]:
        return {
            "available": False,
            "devices": [],
            "error": "Microfono desactivado en configuracion.",
        }

    try:
        import sounddevice as sd
    except ImportError:
        return {
            "available": False,
            "devices": [],
            "error": "sounddevice no esta instalado.",
        }

    try:
        raw_devices = sd.query_devices()
        default_input = None
        try:
            default_input = sd.default.device[0]
        except Exception:
            default_input = None

        devices = []
        for index, device in enumerate(raw_devices):
            max_input_channels = int(device.get("max_input_channels", 0))
            if max_input_channels <= 0:
                continue

            devices.append(
                {
                    "id": index,
                    "name": str(device.get("name", f"Input {index}")),
                    "channels": max_input_channels,
                    "default": index == default_input,
                }
            )

        return {
            "available": bool(devices),
            "devices": devices,
            "error": None if devices else "No se encontraron dispositivos de entrada.",
        }
    except Exception as error:
        return {
            "available": False,
            "devices": [],
            "error": f"No se pudieron listar dispositivos: {error}",
        }


def record_microphone_to_file(
    duration_seconds: int | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    duration = normalize_record_seconds(
        duration_seconds,
        settings["mic_default_record_seconds"],
        settings["mic_max_record_seconds"],
    )
    base_response = {
        "success": False,
        "engine": settings["mic_engine"],
        "duration_seconds": duration,
        "sample_rate": settings["mic_sample_rate"],
        "channels": settings["mic_channels"],
        "output_path": None,
        "error": None,
    }

    if not settings["mic_enabled"]:
        return {**base_response, "error": "Microfono desactivado en configuracion."}

    try:
        import numpy as np
        import sounddevice as sd
    except ImportError:
        return {
            **base_response,
            "error": "sounddevice o numpy no estan instalados.",
        }

    target_path = _resolve_output_path(output_path)

    try:
        frames = duration * settings["mic_sample_rate"]
        recording = sd.rec(
            frames,
            samplerate=settings["mic_sample_rate"],
            channels=settings["mic_channels"],
            dtype="float32",
            device=settings["mic_input_device"],
        )
        sd.wait()

        pcm = np.clip(recording, -1.0, 1.0)
        pcm = (pcm * 32767).astype(np.int16)
        with wave.open(str(target_path), "wb") as wav_file:
            wav_file.setnchannels(settings["mic_channels"])
            wav_file.setsampwidth(2)
            wav_file.setframerate(settings["mic_sample_rate"])
            wav_file.writeframes(pcm.tobytes())

        return {
            **base_response,
            "success": True,
            "output_path": str(target_path),
            "error": None,
        }
    except Exception as error:
        return {
            **base_response,
            "error": f"No se pudo grabar audio del microfono: {error}",
        }


def _resolve_output_path(output_path: str | None) -> Path:
    if output_path is None:
        return build_voice_input_path(safe_wav_filename("microphone"))

    candidate = Path(output_path)
    if candidate.name != candidate.name.replace("..", ""):
        return build_voice_input_path(safe_wav_filename("microphone"))

    return build_voice_input_path(candidate.name)
