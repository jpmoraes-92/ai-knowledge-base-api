from pydantic import BaseModel, Field
from typing import Optional, List

class DocumentUploadRequest(BaseModel):
    title: str = Field(..., description="Título do documento", json_schema_extra={"example": "Manual de RH"})
    content: str = Field(..., min_length=10, description="O texto completo do documento")
    source: Optional[str] = Field(default="upload")
    user_id: str = Field(..., description="ID do usuário proprietário do documento")

class DocumentUploadResponse(BaseModel):
    document_id: str
    total_chunks: int
    embedding_model: str
    user_id: str

class QuestionRequest(BaseModel):
    question: str = Field(..., json_schema_extra={"example": "Quantos dias de férias eu tenho direito?"})
    top_k: int = Field(default=3, ge=1, le=10, description="Quantos trechos recuperar")
    session_id: Optional[str] = Field(default=None, description="ID da sessão para manter o histórico de conversa")
    user_id: str = Field(..., description="ID do usuário fazendo a pergunta")

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
    user_id: str

class AnalyticsResponse(BaseModel):
    results: List[DocumentAnalytics]


# ============ Authentication Schemas ============

class TokenRequest(BaseModel):
    username: str = Field(..., description="Nome de usuário ou email")
    password: str = Field(..., description="Senha do usuário")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Tipo de token")
    user_id: str = Field(..., description="ID do usuário autenticado")
    expires_in: int = Field(..., description="Tempo de expiração em segundos")