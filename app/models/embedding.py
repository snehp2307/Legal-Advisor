from sentence_transformers import SentenceTransformer
from app.utils.config import EMBEDDING_MODEL_NAME


class EmbeddingModel:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        
    def encode(self, texts):
        return self.model.encode(texts,show_progress_bar=False)