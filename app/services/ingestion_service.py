import fitz
import logging
from fastapi import HTTPException

from app.services.openai_service import openai_service
from app.services.vector_service import vector_service
from app.services.mongo_service import mongo_service
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def smart_chunker(text: str, chunk_size: int = 1000, overlap: int = 150):
    """
    Divide o texto em pedaços com um limite de caracteres, 
    garantindo uma sobreposição (overlap) e evitando cortar palavras ao meio.
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        # Se chegamos no final do texto, pega o resto e encerra
        if end >= text_length:
            chunks.append(text[start:].strip())
            break

        # Procura o último espaço vazio ANTES do limite do chunk, 
        # para não fatiar uma palavra pela metade.
        last_space = text.rfind(' ', start, end)
        if last_space != -1 and last_space > start:
            end = last_space

        # Adiciona o chunk validado
        chunks.append(text[start:end].strip())

        # O INÍCIO DO PRÓXIMO CHUNK:
        # Volta o cursor no texto baseado no tamanho do overlap
        start = end - overlap
        
        # Como o overlap pode ter caído no meio de uma palavra, 
        # avançamos até o próximo espaço vazio.
        if start < text_length:
            first_space = text.find(' ', start, end)
            if first_space != -1:
                start = first_space + 1

    return [c for c in chunks if c] # Retorna removendo possíveis chunks vazios

class IngestionService:
    async def process_document(self, title: str, content: str, source: str):
        chunks = smart_chunker(content, chunk_size=1000, overlap=150)
        
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
            # Novo bloco de proteção para blindar o PyMuPDF
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
            except Exception:
                raise ValueError("O arquivo enviado está corrompido ou não é um PDF válido.")
                
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