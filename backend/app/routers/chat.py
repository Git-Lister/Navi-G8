from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import get_current_user
from ..models.user import User
from ..services import ollama_service

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    model: str | None = None  # optional override

class ChatMessage(BaseModel):
    role: str
    content: str

@router.post("")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Stream a response from Ollama for the given user message.
    The user is authenticated via Bearer token.
    """
    # Prepare messages in OpenAI format
    messages = [{"role": "user", "content": request.message}]

    # Use default model from env if not specified
    model = request.model or ollama_service.DEFAULT_MODEL

    # Return streaming response
    return StreamingResponse(
        ollama_service.generate_stream(messages, model=model),
        media_type="text/plain"
    )