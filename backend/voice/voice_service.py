from typing import Any, BinaryIO

from assistant.brain import handle_message
from assistant.settings import get_settings
from voice.audio_utils import ensure_voice_storage, save_upload_file
from voice.microphone_capture import (
    is_microphone_available,
    list_input_devices,
    record_microphone_to_file,
)
from voice.speech_to_text import is_stt_available, transcribe_audio_file
from voice.text_to_speech import is_tts_available, speak_text, synthesize_to_file


def get_voice_status() -> dict[str, Any]:
    settings = get_settings()
    storage = ensure_voice_storage()
    return {
        "voice_enabled": settings["voice_enabled"],
        "stt": is_stt_available(),
        "tts": is_tts_available(),
        "mic": get_microphone_status(),
        "storage_path": str(storage["base"]),
    }


def get_microphone_status() -> dict[str, Any]:
    settings = get_settings()
    availability = is_microphone_available()
    return {
        "mic_enabled": settings["mic_enabled"],
        "enabled": settings["mic_enabled"],
        "available": availability["available"],
        "engine": settings["mic_engine"],
        "sample_rate": settings["mic_sample_rate"],
        "channels": settings["mic_channels"],
        "default_record_seconds": settings["mic_default_record_seconds"],
        "max_record_seconds": settings["mic_max_record_seconds"],
        "error": availability["error"],
    }


def record_from_microphone(duration_seconds: int | None = None) -> dict[str, Any]:
    return record_microphone_to_file(duration_seconds=duration_seconds)


def process_microphone_chat(
    duration_seconds: int | None = None,
    speak_response: bool = False,
) -> dict[str, Any]:
    recording = record_from_microphone(duration_seconds)
    if not recording["success"] or not recording["output_path"]:
        return {
            "status": "error",
            "recording": recording,
            "recorded_audio_path": None,
            "transcribed_text": None,
            "assistant_response": None,
            "brain_status": None,
            "audio": None,
            "details": {"recording": recording},
        }

    response = process_voice_chat(recording["output_path"], speak_response=speak_response)
    response["recording"] = recording
    response["recorded_audio_path"] = recording["output_path"]
    _delete_recording_if_configured(recording["output_path"])
    return response


def transcribe_uploaded_audio(file_obj: BinaryIO, filename: str) -> dict[str, Any]:
    saved = save_upload_file(file_obj, filename)
    if saved["error"]:
        return {
            "saved_path": None,
            "transcription": {
                "available": False,
                "engine": get_settings()["stt_engine"],
                "model": get_settings()["stt_model"],
                "language": get_settings()["stt_language"],
                "text": None,
                "segments": [],
                "error": saved["error"],
            },
        }

    transcription = transcribe_audio_file(str(saved["path"]))
    _delete_input_if_configured(saved["path"])
    return {
        "saved_path": saved["path"],
        "transcription": transcription,
    }


def generate_tts_response(text: str, speak_response: bool = False) -> dict[str, Any]:
    if speak_response:
        return speak_text(text)
    return synthesize_to_file(text)


def process_voice_chat(audio_file_path: str, speak_response: bool = False) -> dict[str, Any]:
    transcription = transcribe_audio_file(audio_file_path)
    if not transcription.get("text"):
        return {
            "status": "error",
            "transcribed_text": None,
            "assistant_response": None,
            "brain_status": None,
            "audio": None,
            "details": {"stt": transcription},
        }

    brain_response = handle_message(transcription["text"])
    audio = None
    if speak_response:
        audio = generate_tts_response(brain_response["message"], speak_response=False)

    return {
        "status": brain_response["status"],
        "transcribed_text": transcription["text"],
        "assistant_response": brain_response,
        "brain_status": brain_response["status"],
        "audio": audio,
        "details": {"stt": transcription},
    }


def process_uploaded_voice_chat(
    file_obj: BinaryIO,
    filename: str,
    speak_response: bool = False,
) -> dict[str, Any]:
    saved = save_upload_file(file_obj, filename)
    if saved["error"]:
        return {
            "status": "error",
            "transcribed_text": None,
            "assistant_response": None,
            "brain_status": None,
            "audio": None,
            "details": {"error": saved["error"]},
        }

    response = process_voice_chat(str(saved["path"]), speak_response=speak_response)
    _delete_input_if_configured(saved["path"])
    return response


def _delete_input_if_configured(path: str | None) -> None:
    if not path:
        return

    settings = get_settings()
    if settings["voice_storage_keep_files"]:
        return

    try:
        from pathlib import Path

        Path(path).unlink(missing_ok=True)
    except OSError:
        pass


def _delete_recording_if_configured(path: str | None) -> None:
    if not path:
        return

    settings = get_settings()
    if settings["mic_save_recordings"]:
        return

    try:
        from pathlib import Path

        Path(path).unlink(missing_ok=True)
    except OSError:
        pass
