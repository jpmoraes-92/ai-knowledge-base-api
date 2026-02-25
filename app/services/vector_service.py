import faiss
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self, dimension: int = 1536, index_path: str = "data/faiss.index"):
        self.dimension = dimension
        self.index_path = index_path
        
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        if os.path.exists(self.index_path):
            logger.info("💾 Carregando índice FAISS salvo no disco...")
            self.index = faiss.read_index(self.index_path)
        else:
            logger.info("🆕 Criando novo índice FAISS in-memory...")
            self.index = faiss.IndexFlatL2(dimension)

    def add_vector(self, vector: list[float]) -> int:
        vec = np.array([vector]).astype("float32")
        vector_id = self.index.ntotal
        self.index.add(vec)
        
        faiss.write_index(self.index, self.index_path)
        return vector_id

    def search(self, query_vector: list[float], top_k: int = 3):
        query = np.array([query_vector]).astype("float32")
        distances, indices = self.index.search(query, top_k)
        return indices[0].tolist(), distances[0].tolist()

vector_service = VectorService()