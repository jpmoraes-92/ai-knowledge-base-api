import random
import logging
import asyncio
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

# --- Fake Mode --- #
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

# --- Real Mode --- #
class RealOpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.embedding_model = settings.embedding_model
        self.llm_model = settings.llm_model
        logger.info("🟢 REAL MODE ATIVADO: Conectado à API oficial da OpenAI!")

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(
            input=texts,
            model=self.embedding_model
        )
        return [data.embedding for data in response.data]

    async def get_embedding(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            input=[text],
            model=self.embedding_model
        )
        return response.data[0].embedding

    async def generate_answer(self, prompt: str) -> tuple[str, int]:
        response = await self.client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": "Você é um assistente corporativo útil, preciso e educado. Responda APENAS com base no contexto fornecido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2 # Respostas mais focadas e menos "criativas/alucinadas"
        )
        
        answer = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        return answer, tokens_used


# --- 3. FACTORY PATTERN: A Injeção de Dependência Dinâmica ---
if settings.use_mock:
    openai_service = MockOpenAIService()
else:
    openai_service = RealOpenAIService()