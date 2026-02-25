from fastapi import APIRouter, status, UploadFile, File, Form, HTTPException
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

@router.post("/pdf", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    title: str = Form(..., description="Título do documento PDF"),
    source: str = Form("upload_pdf"),
    file: UploadFile = File(...)
):
    """Rota específica para upload de arquivos PDF"""
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos.")
        
    file_bytes = await file.read()
    
    result = await ingestion_service.process_pdf(
        title=title,
        file_bytes=file_bytes,
        source=source
    )
    return result