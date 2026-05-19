from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_chatbot_service
from app.schemas.chatbot import ChatbotAnswerResponse, ChatbotQuestionRequest
from app.services.chatbot_service import ChatbotService

router = APIRouter()


@router.post(
    "/ask",
    summary="Chatbot experto en teoría del riesgo",
    response_model=ChatbotAnswerResponse,
)
async def ask_chatbot(
    payload: ChatbotQuestionRequest,
    service: ChatbotService = Depends(get_chatbot_service),
) -> dict:
    return service.answer_question(
        question=payload.question,
        mode=payload.mode,
        module=payload.module,
    )
