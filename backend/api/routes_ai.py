from fastapi import APIRouter
from pydantic import BaseModel, Field

from assistant.local_ai import get_ollama_models, get_ollama_status, set_ollama_model


router = APIRouter(prefix="/ai", tags=["ai"])


class ModelRequest(BaseModel):
    model: str = Field(..., min_length=1)


@router.get("/status")
def ai_status() -> dict[str, object]:
    return get_ollama_status()


@router.get("/models")
def ai_models() -> dict[str, object]:
    return get_ollama_models()


@router.post("/model")
def ai_model(request: ModelRequest) -> dict[str, object]:
    return set_ollama_model(request.model)
