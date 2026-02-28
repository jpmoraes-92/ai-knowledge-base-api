from fastapi import APIRouter, status, Depends
from fastapi.responses import StreamingResponse
from app.models.schemas import QuestionRequest, QuestionResponse
from app.services.rag_service import rag_service
from app.core.security import get_current_user_id

router = APIRouter(prefix="/api/v1/questions", tags=["Questions & RAG"])

@router.post("", response_model=QuestionResponse, status_code=status.HTTP_200_OK)
async def ask_question(
    request: QuestionRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Rota Síncrona Clássica"""
    result = await rag_service.answer_question(
        question=request.question,
        top_k=request.top_k,
        session_id=request.session_id,
        user_id=user_id
    )
    return result

@router.post("/stream", status_code=status.HTTP_200_OK)
async def ask_question_stream(
    request: QuestionRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Rota de Streaming (Server-Sent Events)"""
    return StreamingResponse(
        rag_service.answer_question_stream(
            question=request.question,
            top_k=request.top_k,
            session_id=request.session_id,
            user_id=user_id
        ),
        media_type="text/plain" 
    )