from fastapi import APIRouter, status
from app.models.schemas import DocumentUploadRequest, DocumentUploadResponse
from app.services.ingestion_service import ingestion_service

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])

@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(request: DocumentUploadRequest):
    result = await ingestion_service.process_document(
        title=request.title,
        content=request.content,
        source=request.source
    )
    return result