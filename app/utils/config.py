import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_HOST=os.getenv("QDRANT_HOST")
QDRANT_PORT=int(os.getenv("QDRANT_PORT",6333))
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

COLLECTION_NAME="legal_docs"

EMBEDDING_MODEL_NAME="BAAI/bge-large-en-v1.5"
TOP_K = 3