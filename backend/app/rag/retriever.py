from app.services.embedding_service import generate_embedding
from app.core.config import QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME
from qdrant_client import QdrantClient


client = QdrantClient(
    host=QDRANT_HOST,
    port=QDRANT_PORT
)


def retrieve_documents(question: str, top_k: int = 5):
    query_vector = generate_embedding(question)

    search_result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        with_payload=True,
        score_threshold=0.3
    )

    documents = []

    for point in search_result.points:
        payload = point.payload
        score = point.score

        if payload and "text" in payload:
            documents.append({
                "text": payload["text"],
                "source": payload.get("source"),
                "page": payload.get("page"),
                "score": score
            })

    print("\n===== SCORES QDRANT =====\n")
    for doc in documents:
        print(f"Score: {doc['score']:.3f} | {doc['text'][:150]}")
        print("-----------------")

    return documents