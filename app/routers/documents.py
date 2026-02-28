import uuid
from fastapi import APIRouter, status, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from app.models.schemas import DocumentUploadRequest, DocumentUploadResponse, DocumentTaskResponse, TaskStatusResponse
from app.services.ingestion_service import ingestion_service
from app.core.security import get_current_user_id

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])

# Banco de dados em memória para rastrear as tarefas (Em produção, usaria o MongoDB/Redis)
TASKS_DB = {}

async def background_process_pdf(task_id: str, title: str, file_bytes: bytes, source: str, user_id: str):
    """Função que vai rodar de forma invisível em background"""
    TASKS_DB[task_id] = "Processing"
    try:
        await ingestion_service.process_pdf(
            title=title,
            file_bytes=file_bytes,
            source=source,
            user_id=user_id
        )
        TASKS_DB[task_id] = "Completed"
    except Exception as e:
        TASKS_DB[task_id] = f"Failed: {str(e)}"

@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: DocumentUploadRequest, 
    user_id: str = Depends(get_current_user_id)
):
    """Rota síncrona mantida para textos curtos"""
    result = await ingestion_service.process_document(
        title=request.title,
        content=request.content,
        source=request.source,
        user_id=user_id
    )
    return result

@router.post("/pdf", response_model=DocumentTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_pdf(
    background_tasks: BackgroundTasks, # 👈 Injeção de dependência mágica do FastAPI
    title: str = Form(..., description="Título do documento PDF"),
    source: str = Form("upload_pdf"),
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    """Rota Assíncrona: Recebe o PDF e processa em Background"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos.")
        
    file_bytes = await file.read()
    task_id = str(uuid.uuid4()) # Gera um ID de protocolo único
    
    TASKS_DB[task_id] = "Queued"
    
    # 👈 Manda o trabalho pesado para a thread secundária!
    background_tasks.add_task(
        background_process_pdf, 
        task_id=task_id, 
        title=title, 
        file_bytes=file_bytes, 
        source=source, 
        user_id=user_id
    )
    
    # Devolve a resposta instantaneamente para o utilizador
    return DocumentTaskResponse(
        task_id=task_id,
        message="O PDF foi recebido e está sendo processado em background.",
        status="Queued"
    )

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, user_id: str = Depends(get_current_user_id)):
    """Consulta o status de processamento do PDF"""
    task_status = TASKS_DB.get(task_id)
    if not task_status:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada ou já expirou.")
    
    return TaskStatusResponse(task_id=task_id, status=task_status)