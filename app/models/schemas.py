from pydantic import BaseModel, Field
from typing import Optional
from typing import List

class DocumentUploadRequest(BaseModel):
    title: str = Field(..., description="Título do documento", example="Manual de RH")
    content: str = Field(..., min_length=10, description="O texto completo do documento")
    source: Optional[str] = Field(default="upload")

class DocumentUploadResponse(BaseModel):
    document_id: str
    total_chunks: int
    embedding_model: str

class QuestionRequest(BaseModel):
    question: str = Field(..., example="Quantos dias de férias eu tenho direito?")
    top_k: int = Field(default=3, ge=1, le=10, description="Quantos trechos recuperar")

class RetrievedChunk(BaseModel):
    chunk_id: str
    text: str
    score: float = Field(..., description="Distância L2 (menor é mais similar)")

class QuestionResponse(BaseModel):
    answer: str
    retrieved_chunks: List[RetrievedChunk]
    tokens_used: int
    latency_ms: int

class DocumentAnalytics(BaseModel):
    document_id: str
    title: str
    total_questions: int
    total_tokens: int

class AnalyticsResponse(BaseModel):
    results: List[DocumentAnalytics]