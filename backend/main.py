from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from config import APP_NAME, APP_VERSION, DATABASE_PATH, SETTINGS_PATH, STORAGE_DIR
from api.routes_actions import router as actions_router
from api.routes_ai import router as ai_router
from api.routes_chat import router as chat_router
from api.routes_memory import router as memory_router
from api.routes_settings import router as settings_router
from api.routes_tools import router as tools_router
from api.routes_voice import router as voice_router
from assistant.local_ai import get_ollama_status
from assistant.memory import init_db
from assistant.pending_actions import count_pending_actions, init_pending_actions_db
from assistant.settings import get_settings
from voice.speech_to_text import is_stt_available
from voice.text_to_speech import is_tts_available
from voice.microphone_capture import is_microphone_available


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    init_pending_actions_db()
    yield


app = FastAPI(
    title="ARVIS Backend",
    description="Backend minimo para el asistente open source ARVIS.",
    version=APP_VERSION,
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, object]:
    ai_status = get_ollama_status(timeout_seconds=0.3)
    settings = get_settings()
    stt_status = is_stt_available()
    tts_status = is_tts_available()
    mic_status = is_microphone_available()

    return {
        "status": "OK",
        "app": APP_NAME,
        "version": APP_VERSION,
        "backend": "running",
        "storage_path": str(STORAGE_DIR),
        "database_exists": DATABASE_PATH.exists(),
        "settings_exists": SETTINGS_PATH.exists(),
        "pending_actions_count": count_pending_actions(),
        "ai_enabled": ai_status["enabled"],
        "ai_available": ai_status["available"],
        "ai_model": ai_status["model"],
        "voice_enabled": settings["voice_enabled"],
        "stt_available": stt_status["available"],
        "tts_available": tts_status["available"],
        "mic_enabled": settings["mic_enabled"],
        "mic_available": mic_status["available"],
    }


app.include_router(chat_router)
app.include_router(actions_router)
app.include_router(ai_router)
app.include_router(tools_router)
app.include_router(memory_router)
app.include_router(settings_router)
app.include_router(voice_router)
