from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel, Field

from voice.voice_service import (
    generate_tts_response,
    get_microphone_status,
    get_voice_status,
    process_microphone_chat,
    process_uploaded_voice_chat,
    record_from_microphone,
    transcribe_uploaded_audio,
)
from voice.microphone_capture import list_input_devices


router = APIRouter(prefix="/voice", tags=["voice"])


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    speak_now: bool = False


class MicRecordRequest(BaseModel):
    duration_seconds: int | None = Field(default=None, ge=1, le=60)


class MicChatRequest(BaseModel):
    duration_seconds: int | None = Field(default=None, ge=1, le=60)
    speak_response: bool = False


@router.get("/status")
def voice_status() -> dict[str, object]:
    return get_voice_status()


@router.post("/stt")
def voice_stt(file: UploadFile = File(...)) -> dict[str, object]:
    return transcribe_uploaded_audio(file.file, file.filename or "audio.wav")


@router.post("/tts")
def voice_tts(request: TTSRequest) -> dict[str, object]:
    return generate_tts_response(request.text, speak_response=request.speak_now)


@router.post("/chat")
def voice_chat(
    file: UploadFile = File(...),
    speak_response: bool = Form(False),
) -> dict[str, object]:
    return process_uploaded_voice_chat(
        file.file,
        file.filename or "audio.wav",
        speak_response=speak_response,
    )


@router.get("/mic/status")
def voice_mic_status() -> dict[str, object]:
    return get_microphone_status()


@router.get("/mic/devices")
def voice_mic_devices() -> dict[str, object]:
    return list_input_devices()


@router.post("/mic/record")
def voice_mic_record(request: MicRecordRequest) -> dict[str, object]:
    return record_from_microphone(request.duration_seconds)


@router.post("/mic/chat")
def voice_mic_chat(request: MicChatRequest) -> dict[str, object]:
    return process_microphone_chat(
        duration_seconds=request.duration_seconds,
        speak_response=request.speak_response,
    )
