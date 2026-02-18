from app.services.embedding_service import generate_embedding
from app.core.config import QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME
from qdrant_client import QdrantClient


client = QdrantClient(
    host=QDRANT_HOST,
    port=QDRANT_PORT
)


def retrieve_documents(question: str, top_k: int = 1):

    query_vector = generate_embedding(question)

    search_result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k
    )

    documents = []

    for hit in search_result.points:
        if hit.payload and "text" in hit.payload:
            documents.append(hit.payload["text"])

    return documents
