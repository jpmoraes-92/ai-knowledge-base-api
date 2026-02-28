import time
from app.services.openai_service import openai_service
from app.services.vector_service import vector_service
from app.services.mongo_service import mongo_service

class RAGService:
    async def answer_question(self, question: str, top_k: int = 3, session_id: str = None, user_id: str = None):
        start_time = time.time()
        
        query_vector = await openai_service.get_embedding(question)
        vector_ids, distances = vector_service.search(query_vector, top_k=top_k)
        
        # O Mongo agora vai filtrar: só devolve se o dono do chunk for o user_id logado
        chunks = await mongo_service.get_chunks_by_vector_ids(vector_ids, user_id=user_id)
        
        if not chunks:
            # Trava de Segurança: Se os vetores mais próximos pertencem a outro usuário, negamos a resposta.
            return {
                "answer": "Não encontrei informações nos seus documentos autorizados para responder a esta pergunta.",
                "retrieved_chunks": [],
                "tokens_used": 0,
                "latency_ms": int((time.time() - start_time) * 1000)
            }
            
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
            session_id=session_id,
            user_id=user_id # Salvando o dono no log
        )
        
        return {
            "answer": answer,
            "retrieved_chunks": retrieved_data,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms
        }
    
    async def answer_question_stream(self, question: str, top_k: int = 3, session_id: str = None, user_id: str = None):
        start_time = time.time()
        
        query_vector = await openai_service.get_embedding(question)
        vector_ids, distances = vector_service.search(query_vector, top_k=top_k)
        chunks = await mongo_service.get_chunks_by_vector_ids(vector_ids, user_id=user_id)
        
        if not chunks:
            yield "Não encontrei informações nos seus documentos autorizados para responder a esta pergunta."
            return
            
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
        
        full_answer = ""
        
        # Consome o gerador assíncrono e devolve os pedaços imediatamente
        async for text_chunk in openai_service.generate_answer_stream(prompt):
            full_answer += text_chunk
            yield text_chunk
            
        # Quando o streaming termina, salvamos no histórico (MongoDB)
        latency_ms = int((time.time() - start_time) * 1000)
        estimated_tokens = (len(prompt) + len(full_answer)) // 4 # Estimativa rápida
        
        await mongo_service.log_conversation(
            question=question,
            answer=full_answer,
            document_ids=list(document_ids),
            retrieved_chunks=retrieved_data,
            tokens_used=estimated_tokens,
            latency_ms=latency_ms,
            session_id=session_id,
            user_id=user_id
        )

rag_service = RAGService()