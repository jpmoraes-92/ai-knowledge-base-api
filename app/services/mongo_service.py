from app.core.database import db
from bson import ObjectId
from datetime import datetime, timezone

class MongoService:
    async def create_document(self, title: str, source: str, total_chunks: int, embedding_model: str, user_id: str) -> str:
        doc = {
            "title": title,
            "source": source,
            "total_chunks": total_chunks,
            "embedding_model": embedding_model,
            "user_id": user_id,  # Salvando o dono do PDF!
            "created_at": datetime.now(timezone.utc)
        }
        result = await db.documents.insert_one(doc)
        return str(result.inserted_id)

    async def save_chunk(self, document_id: str, chunk_index: int, text: str, vector_id: int, user_id: str):
        chunk = {
            "document_id": ObjectId(document_id),
            "chunk_index": chunk_index,
            "text": text,
            "vector_id": vector_id,
            "user_id": user_id  
        }
        await db.chunks.insert_one(chunk)

    async def get_chunks_by_vector_ids(self, vector_ids: list[int], user_id: str):

        clean_vector_ids = [int(vid) for vid in vector_ids if int(vid) != -1]
        
        if not clean_vector_ids:
            return []

        cursor = db.chunks.find({"vector_id": {"$in": clean_vector_ids}, "user_id": user_id})
        chunks = await cursor.to_list(length=len(clean_vector_ids))
        
        chunk_map = {chunk["vector_id"]: chunk for chunk in chunks}
        ordered_chunks = [chunk_map[vid] for vid in clean_vector_ids if vid in chunk_map]
        
        return ordered_chunks

    async def get_recent_history(self, session_id: str, limit: int = 3):
        if not session_id:
            return []
        
        cursor = db.conversations.find({"session_id": session_id}).sort("created_at", -1).limit(limit)
        history = await cursor.to_list(length=limit)
        
        return list(reversed(history))

    async def log_conversation(self, question: str, answer: str, document_ids: list[str], retrieved_chunks: list[dict], tokens_used: int, latency_ms: int, session_id: str = None, user_id: str = None):
        conversa = {
            "session_id": session_id,
            "user_id": user_id, # Registrando quem fez a pergunta
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
            {"$unwind": "$document_ids"},
            
            {"$group": {
                "_id": "$document_ids",
                "total_questions": {"$sum": 1},
                "total_tokens": {"$sum": "$tokens_used"}
            }},
            
            {"$lookup": {
                "from": "documents",
                "localField": "_id",
                "foreignField": "_id",
                "as": "doc_info"
            }},
            
            {"$unwind": "$doc_info"},
            
            {"$project": {
                "document_id": {"$toString": "$_id"},
                "title": "$doc_info.title",
                "total_questions": 1,
                "total_tokens": 1,
                "_id": 0
            }},
            
            {"$sort": {"total_questions": -1}}
        ]
        
        cursor = db.conversations.aggregate(pipeline)
        return await cursor.to_list(length=100)

mongo_service = MongoService()