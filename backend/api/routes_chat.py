from fastapi import APIRouter
from pydantic import BaseModel, Field

from assistant.brain import handle_message


router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


@router.post("/chat")
def chat(request: ChatRequest) -> dict:
    return handle_message(request.message)
