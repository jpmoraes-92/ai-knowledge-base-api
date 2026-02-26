import time
from app.services.openai_service import openai_service
from app.services.vector_service import vector_service
from app.services.mongo_service import mongo_service

class RAGService:
    async def answer_question(self, question: str, top_k: int = 3, session_id: str = None):
        start_time = time.time()
        
        query_vector = await openai_service.get_embedding(question)
        vector_ids, distances = vector_service.search(query_vector, top_k=top_k)
        chunks = await mongo_service.get_chunks_by_vector_ids(vector_ids)
        
        retrieved_data = []
        document_ids = set()
        context_texts = []
        
        for chunk, score in zip(chunks, distances):
            retrieved_data.append({
                "chunk_id": str(chunk["_id"]),
                "text": chunk["text"],
                "score": float(score)
            })
            document_ids.add(str(chunk["document_id"]))
            context_texts.append(chunk["text"])
            
        contexto_junto = "\n---\n".join(context_texts)
        
        history = await mongo_service.get_recent_history(session_id)
        history_text = ""
        
        if history:
            history_text = "Histórico da Conversa:\n"
            for msg in history:
                history_text += f"Usuário: {msg['question']}\nIA: {msg['answer']}\n\n"
        
        prompt = (
            f"Use o contexto abaixo para responder à pergunta.\n\n"
            f"Contexto Recuperado:\n{contexto_junto}\n\n"
            f"{history_text}"
            f"Pergunta Atual: {question}"
        )
        
        answer, tokens_used = await openai_service.generate_answer(prompt)
        
        latency_ms = int((time.time() - start_time) * 1000)
        await mongo_service.log_conversation(
            question=question,
            answer=answer,
            document_ids=list(document_ids),
            retrieved_chunks=retrieved_data,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            session_id=session_id 
        )
        
        return {
            "answer": answer,
            "retrieved_chunks": retrieved_data,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms
        }

rag_service = RAGService()