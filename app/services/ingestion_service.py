import fitz
import logging
from fastapi import HTTPException

from app.services.openai_service import openai_service
from app.services.vector_service import vector_service
from app.services.mongo_service import mongo_service
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def simple_chunker(text: str, chunk_size: int = 1000):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

class IngestionService:
    async def process_document(self, title: str, content: str, source: str):
        chunks = simple_chunker(content)
        
        doc_id = await mongo_service.create_document(
            title=title, 
            source=source, 
            total_chunks=len(chunks), 
            embedding_model=settings.embedding_model
        )
        
        try:
            embeddings = await openai_service.get_embeddings(chunks)
        except Exception as e:
            logger.error(f"Erro na OpenAI: {str(e)}")
            raise HTTPException(
                status_code=502, 
                detail=f"Falha ao gerar embeddings via OpenAI. Erro original: {str(e)}"
            )
        
        for i, (text, vector) in enumerate(zip(chunks, embeddings)):
            vector_id = vector_service.add_vector(vector)
            await mongo_service.save_chunk(doc_id, i, text, vector_id)
            
        return {
            "document_id": doc_id,
            "total_chunks": len(chunks),
            "embedding_model": settings.embedding_model
        }

    async def process_pdf(self, title: str, file_bytes: bytes, source: str):
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            full_text = ""
            
            for page in doc:
                full_text += page.get_text() + "\n"
                
            if not full_text.strip():
                raise ValueError("O PDF não possui camada de texto digital. Parecem ser imagens escaneadas.")
                
            logger.info(f"📄 PDF lido com sucesso: {len(full_text)} caracteres extraídos.")
            
            return await self.process_document(title=title, content=full_text, source=source)
            
        except ValueError as ve:
            logger.warning(f"Aviso de conteúdo: {str(ve)}")
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error(f"Erro inesperado ao ler PDF: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Erro interno ao processar PDF: {str(e)}")

ingestion_service = IngestionService()