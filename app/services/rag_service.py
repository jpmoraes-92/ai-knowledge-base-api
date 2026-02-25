import time
from app.services.openai_service import openai_service
from app.services.vector_service import vector_service
from app.services.mongo_service import mongo_service

class RAGService:
    async def answer_question(self, question: str, top_k: int = 3):
        start_time = time.time()
        
        # 1. Transforma a pergunta do usuário em um vetor matemático
        query_vector = await openai_service.get_embedding(question)
        
        # 2. Pede ao FAISS os IDs dos vetores mais próximos (busca semântica)
        vector_ids, distances = vector_service.search(query_vector, top_k=top_k)
        
        # 3. Pede ao Mongo os textos originais correspondentes a esses IDs
        chunks = await mongo_service.get_chunks_by_vector_ids(vector_ids)
        
        # 4. Prepara os dados de fonte (Provenance) para retornar ao usuário
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
            
        # 5. Monta o Prompt com o Contexto + Pergunta
        contexto_junto = "\n---\n".join(context_texts)
        prompt = f"Use o contexto abaixo para responder à pergunta.\n\nContexto:\n{contexto_junto}\n\nPergunta: {question}"
        
        # 6. Pede a resposta para a LLM (nosso Mock)
        answer, tokens_used = await openai_service.generate_answer(prompt)
        
        # 7. Calcula latência e salva histórico no Mongo para o Analytics
        latency_ms = int((time.time() - start_time) * 1000)
        await mongo_service.log_conversation(
            question=question,
            answer=answer,
            document_ids=list(document_ids),
            retrieved_chunks=retrieved_data,
            tokens_used=tokens_used,
            latency_ms=latency_ms
        )
        
        return {
            "answer": answer,
            "retrieved_chunks": retrieved_data,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms
        }

rag_service = RAGService()