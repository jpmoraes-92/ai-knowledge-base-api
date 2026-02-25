from fastapi import FastAPI
from app.routers import documents
from app.routers import questions
from app.routers import analytics

app = FastAPI(
    title="AI Knowledge Base API",
    description="Backend RAG com FastAPI, MongoDB e FAISS",
    version="1.0.0"
)

app.include_router(documents.router) 
app.include_router(questions.router)
app.include_router(analytics.router)

@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "message": "Laboratório de IA operante!"}