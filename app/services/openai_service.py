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
        answer = "🤖 [MOCK LLM]: Esta é uma resposta simulada!"
        tokens_used = random.randint(150, 500) 
        return answer, tokens_used

    # NOVO: Método de Streaming (Mock)
    async def generate_answer_stream(self, prompt: str):
        answer = "🤖 [MOCK LLM]: Esta é uma resposta simulada em streaming! Se eu fosse o GPT-4, eu teria lido os documentos e respondido palavra por palavra..."
        words = answer.split(" ")
        for word in words:
            await asyncio.sleep(0.05) # Simula o tempo de digitação
            yield word + " "

# --- Real Mode --- #
class RealOpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.embedding_model = settings.embedding_model
        self.llm_model = settings.llm_model
        logger.info("🟢 REAL MODE ATIVADO: Conectado à API oficial da OpenAI!")

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(input=texts, model=self.embedding_model)
        return [data.embedding for data in response.data]

    async def get_embedding(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(input=[text], model=self.embedding_model)
        return response.data[0].embedding

    async def generate_answer(self, prompt: str) -> tuple[str, int]:
        response = await self.client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": "Você é um assistente corporativo útil. Responda APENAS com base no contexto fornecido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content, response.usage.total_tokens

    # NOVO: Método de Streaming (Real)
    async def generate_answer_stream(self, prompt: str):
        response = await self.client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": "Você é um assistente corporativo útil. Responda APENAS com base no contexto fornecido."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            stream=True # O segredo do streaming está aqui!
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

# --- FACTORY PATTERN ---
if settings.use_mock:
    openai_service = MockOpenAIService()
else:
    openai_service = RealOpenAIService()