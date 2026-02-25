import faiss
import numpy as np

class VectorService:
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        # IndexFlatL2 = Busca exata usando Distância Euclidiana
        self.index = faiss.IndexFlatL2(dimension)

    def add_vector(self, vector: list[float]) -> int:
        vec = np.array([vector]).astype("float32")
        vector_id = self.index.ntotal
        self.index.add(vec)
        return vector_id

    def search(self, query_vector: list[float], top_k: int = 3):
        query = np.array([query_vector]).astype("float32")
        distances, indices = self.index.search(query, top_k)
        # indices[0] retorna os IDs, distances[0] retorna o score L2
        return indices[0].tolist(), distances[0].tolist()

vector_service = VectorService()