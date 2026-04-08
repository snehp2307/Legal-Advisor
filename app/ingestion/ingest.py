import json
from qdrant_client.models import VectorParams, Distance
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings

from app.models.embedding import EmbeddingModel
from app.services.vector_store import client
from app.utils.config import COLLECTION_NAME


def get_semantic_chunks(text: str, chunker) -> list[str]:
    if not text or not text.strip():
        return []
    try:
        docs = chunker.create_documents([text])
        return [doc.page_content for doc in docs if doc.page_content.strip()]
    except:
        return [text]


def normalize_data(data, source):
    normalized = []
    for item in data:
        try:
            if source == "constitution":
                normalized.append({
                    "type": "constitution",
                    "id": f"Article {item['article']}",
                    "title": item["title"],
                    "text": item["description"]
                })
            elif source == "bns":
                normalized.append({
                    "type": "bns",
                    "id": f"Section {item['section']}",
                    "title": item["title"],
                    "text": item["description"]
                })
            elif source == "crpc":
                normalized.append({
                    "type": "crpc",
                    "id": f"Section {item['section']}",
                    "title": item["section_title"],
                    "text": item["section_desc"]
                })
            elif source == "cpc":
                normalized.append({
                    "type": "cpc",
                    "id": f"Section {item['section']}",
                    "title": item["title"],
                    "text": item["description"]
                })
            elif source == "ida":
                normalized.append({
                    "type": "ida",
                    "id": f"Section {item['section']}",
                    "title": item["title"],
                    "text": item["description"]
                })
            elif source == "mva":
                normalized.append({
                    "type": "mva",
                    "id": f"Section {item['section']}",
                    "title": item["title"],
                    "text": item["description"]
                })
        except:
            continue
    return normalized


if __name__ == "__main__":
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=1024,
            distance=Distance.COSINE
        )
    )
    print("Collection reset complete")
   

    all_data = []

    files = [
        ("constitution.json", "constitution"),
        ("bns.json", "bns"),
        ("crpc.json", "crpc"),
        ("cpc.json", "cpc"),
        ("ida.json", "ida"),
        ("mva.json", "mva"),
    ]

    for file_name, source in files:
        try:
            with open(f"data/{file_name}", "r") as f:
                data = json.load(f)
                normalized = normalize_data(data, source)
                all_data.extend(normalized)
        except:
            print(f"Skipping {file_name}")

  
    print("Loading embedding model...")
    hf_embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-en-v1.5" 
    )
    chunker = SemanticChunker(
        embeddings=hf_embeddings,
        breakpoint_threshold_type="percentile",  # splits at biggest semantic jumps
        breakpoint_threshold_amount=85           # top 15% dissimilar points = new chunk
    )

    embedder = EmbeddingModel()
    processed_data = []

    print("Chunking and enriching data...")

    for i, item in enumerate(all_data):
        chunks = get_semantic_chunks(item["text"], chunker)

        for chunk in chunks:
            enriched_text = f"passage: {item['id']}: {item['title']}. {chunk}"
            processed_data.append({
                "type": item["type"],
                "id": item["id"],
                "title": item["title"],
                "text": enriched_text
            })

        if i % 100 == 0:
            print(f"Chunked {i}/{len(all_data)} items...")

    texts = [item["text"] for item in processed_data]

    print(f"Total chunks to embed: {len(texts)}")
    print("Embedding data...")
    
    vectors = []
    for i in range(0, len(texts), 64):
       batch = texts[i:i + 64]
       vectors.extend(embedder.encode(batch))
       print(f"Embedded {min(i + 64, len(texts))}/{len(texts)} chunks...")

    points = [
        {
            "id": i,
            "vector": vector,
            "payload": {
                "type": item["type"],
                "id": item["id"],
                "title": item["title"],
                "text": item["text"]
            }
        }
        for i, (item, vector) in enumerate(zip(processed_data, vectors))
    ]

    print("Uploading to Qdrant...")

    BATCH_SIZE = 100
    total_batches = (len(points) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(points), BATCH_SIZE):
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points[i:i + BATCH_SIZE]
        )
        print(f"Inserted batch {i // BATCH_SIZE + 1}/{total_batches}")

    print("Data inserted successfully!")