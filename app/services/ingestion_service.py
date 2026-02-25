from app.services.openai_service import openai_service
from app.services.vector_service import vector_service
from app.services.mongo_service import mongo_service
from app.core.config import settings

# Um chunker simples para separar textos muito grandes
def simple_chunker(text: str, chunk_size: int = 1000):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

class IngestionService:
    async def process_document(self, title: str, content: str, source: str):
        # 1. Cortar o texto em Chunks
        chunks = simple_chunker(content)
        
        # 2. Criar o documento pai no MongoDB
        doc_id = await mongo_service.create_document(
            title=title, 
            source=source, 
            total_chunks=len(chunks), 
            embedding_model=settings.embedding_model
        )
        
        # 3. Chamar a OpenAI para gerar os vetores matemáticos
        embeddings = await openai_service.get_embeddings(chunks)
        
        # 4. Salvar vetores no FAISS e o texto no Mongo (conectados pelo vector_id)
        for i, (text, vector) in enumerate(zip(chunks, embeddings)):
            vector_id = vector_service.add_vector(vector)
            await mongo_service.save_chunk(doc_id, i, text, vector_id)
            
        return {
            "document_id": doc_id,
            "total_chunks": len(chunks),
            "embedding_model": settings.embedding_model
        }

ingestion_service = IngestionService()