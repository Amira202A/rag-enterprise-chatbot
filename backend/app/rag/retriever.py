from app.services.embedding_service import generate_embedding
from app.core.config import QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME
from qdrant_client import QdrantClient


# connexion Qdrant
client = QdrantClient(
    host=QDRANT_HOST,
    port=QDRANT_PORT
)


def retrieve_documents(question: str, top_k: int = 5):

    # 1️⃣ embedding de la question
    query_vector = generate_embedding(question)

    # 2️⃣ 🔥 recherche vectorielle avec seuil de similarité
    search_result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        with_payload=True,
        score_threshold=0.7   # 🔥 FILTRE CRITIQUE
    )

    documents = []

    # 3️⃣ extraction des documents
    for point in search_result.points:

        payload = point.payload
        score = point.score  # 🔥 utile pour debug

        if payload and "text" in payload:
            documents.append({
                "text": payload["text"],
                "source": payload.get("source"),
                "page": payload.get("page"),
                "score": score   # 🔥 optionnel (debug / amélioration future)
            })

    # 🔍 DEBUG (très utile)
    print("\n===== SCORES QDRANT =====\n")
    for doc in documents:
        print(f"Score: {doc['score']:.3f}")
        print(doc["text"][:200])
        print("\n-----------------\n")

    return documents