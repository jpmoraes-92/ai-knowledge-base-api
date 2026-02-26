from fastapi import APIRouter, status
from app.models.schemas import QuestionRequest, QuestionResponse
from app.services.rag_service import rag_service

router = APIRouter(prefix="/api/v1/questions", tags=["Questions & RAG"])

@router.post("", response_model=QuestionResponse, status_code=status.HTTP_200_OK)
async def ask_question(request: QuestionRequest):
    result = await rag_service.answer_question(
        question=request.question,
        top_k=request.top_k,
        session_id=request.session_id 
    )
    return result