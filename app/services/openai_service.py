import random
import logging
import asyncio

logger = logging.getLogger(__name__)

class MockOpenAIService:
    def __init__(self):
        self.dimension = 1536 
        logger.warning("⚠️ MOCK MODE ATIVADO: Usando OpenAI falsa para economizar custos!")

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        await asyncio.sleep(0.5) 
        
        return [[random.uniform(-1.0, 1.0) for _ in range(self.dimension)] for _ in texts]

    async def get_embedding(self, text: str) -> list[float]:
        await asyncio.sleep(0.2)
        return [random.uniform(-1.0, 1.0) for _ in range(self.dimension)]

    async def generate_answer(self, prompt: str) -> tuple[str, int]:
        await asyncio.sleep(1)
        
        answer = (
            "🤖 [MOCK LLM]: Esta é uma resposta simulada! \n"
            "Se eu fosse o GPT-4, eu teria lido os documentos recuperados no FAISS "
            "e respondido a sua pergunta com base neles. \n\n"
            f"Tamanho do prompt recebido: {len(prompt)} caracteres."
        )
        tokens_used = random.randint(150, 500) 
        
        return answer, tokens_used

openai_service = MockOpenAIService()