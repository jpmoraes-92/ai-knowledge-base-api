import random
import logging
import asyncio

logger = logging.getLogger(__name__)

class MockOpenAIService:
    def __init__(self):
        self.dimension = 1536  # O mesmo tamanho do text-embedding-3-small
        logger.warning("⚠️ MOCK MODE ATIVADO: Usando OpenAI falsa para economizar custos!")

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        # Simula o tempo de rede da API real
        await asyncio.sleep(0.5) 
        
        # Gera uma lista de vetores aleatórios com exatos 1536 números cada
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
        # Inventa um custo de tokens para nosso Analytics funcionar
        tokens_used = random.randint(150, 500) 
        
        return answer, tokens_used

# Exportamos a instância falsa com o MESMO NOME da verdadeira.
# Assim, NENHUM outro arquivo do projeto precisa ser alterado!
openai_service = MockOpenAIService()