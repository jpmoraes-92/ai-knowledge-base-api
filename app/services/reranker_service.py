import logging
import torch # 👈 Importamos o PyTorch
from sentence_transformers import CrossEncoder

# ⚡ OTIMIZAÇÃO EXTREMA PARA DOCKER/WINDOWS:
# Força o PyTorch a usar apenas 1 ou 2 threads, evitando que ele trave a CPU do PC inteiro.
torch.set_num_threads(2)

logger = logging.getLogger(__name__)

class RerankerService:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        logger.info(f"⏳ Carregando modelo de Re-Ranking local: {model_name}...")
        self.model = CrossEncoder(model_name, max_length=512)
        logger.info("✅ Modelo de Re-Ranking carregado com sucesso!")

    def rerank(self, query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
        if not chunks:
            return []

        pairs = [[query, chunk["text"]] for chunk in chunks]
        scores = self.model.predict(pairs)

        for i, chunk in enumerate(chunks):
            chunk["rerank_score"] = float(scores[i])

        ranked_chunks = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
        return ranked_chunks[:top_k]

reranker_service = RerankerService()