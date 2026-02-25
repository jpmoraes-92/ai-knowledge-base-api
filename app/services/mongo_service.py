from app.core.database import db
from bson import ObjectId
from datetime import datetime, timezone

class MongoService:
    async def create_document(self, title: str, source: str, total_chunks: int, embedding_model: str) -> str:
        doc = {
            "title": title,
            "source": source,
            "total_chunks": total_chunks,
            "embedding_model": embedding_model,
            "created_at": datetime.now(timezone.utc)
        }
        result = await db.documents.insert_one(doc)
        return str(result.inserted_id)

    async def save_chunk(self, document_id: str, chunk_index: int, text: str, vector_id: int):
        chunk = {
            "document_id": ObjectId(document_id),
            "chunk_index": chunk_index,
            "text": text,
            "vector_id": vector_id # O Elo de Ligação com o FAISS!
        }
        await db.chunks.insert_one(chunk)

    async def get_chunks_by_vector_ids(self, vector_ids: list[int]):
        # Busca no Mongo todos os chunks cujo vector_id esteja na lista retornada pelo FAISS
        cursor = db.chunks.find({"vector_id": {"$in": vector_ids}})
        chunks = await cursor.to_list(length=len(vector_ids))
        
        # O FAISS retorna ordenado por relevância, mas o Mongo não garante a ordem do $in.
        # Vamos reordenar os resultados para bater com a ordem do FAISS.
        chunk_map = {chunk["vector_id"]: chunk for chunk in chunks}
        ordered_chunks = [chunk_map[vid] for vid in vector_ids if vid in chunk_map]
        
        return ordered_chunks

    async def log_conversation(self, question: str, answer: str, document_ids: list[str], retrieved_chunks: list[dict], tokens_used: int, latency_ms: int):
        conversa = {
            "question": question,
            "answer": answer,
            "document_ids": [ObjectId(doc_id) for doc_id in document_ids],
            "retrieved_chunks": retrieved_chunks,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
            "created_at": datetime.now(timezone.utc)
        }
        await db.conversations.insert_one(conversa)

    async def get_document_analytics(self):
        pipeline = [
            # 1. Separa o array de documentos usados (se uma pergunta usou 3 docs, vira 3 linhas)
            {"$unwind": "$document_ids"},
            
            # 2. Agrupa pelo ID do documento, contando perguntas e somando tokens
            {"$group": {
                "_id": "$document_ids",
                "total_questions": {"$sum": 1},
                "total_tokens": {"$sum": "$tokens_used"}
            }},
            
            # 3. Faz um "JOIN" (lookup) com a coleção de documentos para pegar o título
            {"$lookup": {
                "from": "documents",
                "localField": "_id",
                "foreignField": "_id",
                "as": "doc_info"
            }},
            
            # 4. Desfaz o array do join
            {"$unwind": "$doc_info"},
            
            # 5. Formata a saída final limpa para o FastAPI (Pydantic)
            {"$project": {
                "document_id": {"$toString": "$_id"},
                "title": "$doc_info.title",
                "total_questions": 1,
                "total_tokens": 1,
                "_id": 0
            }},
            
            # 6. Ordena dos mais consultados para os menos
            {"$sort": {"total_questions": -1}}
        ]
        
        cursor = db.conversations.aggregate(pipeline)
        return await cursor.to_list(length=100)

mongo_service = MongoService()