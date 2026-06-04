from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from assistant.permissions import PermissionLevel
from assistant.settings import get_settings, reset_settings, update_settings


router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsPatch(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ollama_enabled: bool | None = None
    ollama_base_url: str | None = None
    ollama_model: str | None = None
    ollama_timeout_seconds: int | None = None
    conversation_history_enabled: bool | None = None
    conversation_history_limit: int | None = None
    pending_action_expiration_minutes: int | None = None
    voice_enabled: bool | None = None
    stt_enabled: bool | None = None
    stt_engine: str | None = None
    stt_model: str | None = None
    stt_language: str | None = None
    stt_device: str | None = None
    stt_compute_type: str | None = None
    tts_enabled: bool | None = None
    tts_engine: str | None = None
    tts_voice: str | None = None
    tts_rate: int | None = None
    tts_volume: float | None = None
    voice_output_format: str | None = None
    voice_storage_keep_files: bool | None = None
    mic_enabled: bool | None = None
    mic_engine: str | None = None
    mic_sample_rate: int | None = None
    mic_channels: int | None = None
    mic_max_record_seconds: int | None = None
    mic_default_record_seconds: int | None = None
    mic_input_device: str | int | None = None
    mic_save_recordings: bool | None = None


@router.get("")
def current_settings() -> dict[str, object]:
    return get_settings()


@router.patch("")
def patch_settings(request: SettingsPatch) -> dict[str, object]:
    return update_settings(request.model_dump(exclude_none=True))


@router.post("/reset")
def reset_current_settings() -> dict[str, object]:
    return reset_settings()


@router.get("/permissions")
def permissions() -> dict[str, list[str]]:
    return {
        "levels": [level.value for level in PermissionLevel],
        "default_policy": [
            "safe actions can run only through allowlisted tools",
            "risky actions require confirmation",
            "dangerous actions are blocked",
        ],
    }
