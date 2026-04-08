from qdrant_client import QdrantClient
from app.utils.config import QDRANT_HOST,QDRANT_PORT

client=QdrantClient(
    host=QDRANT_HOST,
    port=QDRANT_PORT
) 