from app.services.embedding_service import generate_embedding
from app.core.config import QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME
from app.rag.clustering import load_kmeans, get_best_clusters, assign_cluster
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny
import numpy as np


client = QdrantClient(
    host=QDRANT_HOST,
    port=QDRANT_PORT
)


def retrieve_documents(question: str, top_k: int = 5, departments: list = None):
    """
    Retrieval avec K-Means clustering + multi-départements :
    1. Génère l'embedding de la question
    2. Cherche dans Qdrant avec filtre departments
    3. Retourne les documents les plus pertinents
    """

    query_vector = generate_embedding(question)

    # ✅ Essayer d'utiliser K-Means
    kmeans = load_kmeans()

    # ✅ Filtre multi-départements
    query_filter = None
    if departments and len(departments) > 0:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="department",
                    match=MatchAny(any=departments)
                )
            ]
        )

    if kmeans:
        print("🎯 K-Means actif — recherche par clusters")

        search_result = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k * 3,
            with_payload=True,
            score_threshold=0.2,
            query_filter=query_filter
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
                    "department": payload.get("department"),
                    "score": score
                })

        # Tri par pertinence
        documents.sort(key=lambda x: x["score"], reverse=True)

        print(f"\n===== SCORES QDRANT (K-Means) =====\n")
        for doc in documents[:top_k]:
            print(f"Score: {doc['score']:.3f} | {doc['text'][:150]}")
            print("-----------------")

        return documents[:top_k]

    else:
        print("⚠️ K-Means non entraîné — recherche vectorielle simple")

        search_result = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
            with_payload=True,
            score_threshold=0.3,
            query_filter=query_filter
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
                    "department": payload.get("department"),
                    "score": score
                })

        print("\n===== SCORES QDRANT =====\n")
        for doc in documents:
            print(f"Score: {doc['score']:.3f} | {doc['text'][:150]}")
            print("-----------------")

        return documents[:top_k]