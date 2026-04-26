from app.services.embedding_service import generate_embedding
from app.core.config import QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME
from app.rag.clustering import load_kmeans
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny, MatchValue
import numpy as np

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def retrieve_documents(question: str, top_k: int = 5, departments: list = None):
    """
    Retrieval intelligent avec support multi-départements.
    - 1 département  → recherche simple filtrée
    - N départements → recherche par département + fusion scored
    """
    query_vector = generate_embedding(question)
    kmeans       = load_kmeans()

    # ─── ADMIN ou aucun filtre ───
    if not departments or len(departments) == 0:
        return _search_qdrant(query_vector, top_k, None, kmeans)

    # ─── 1 seul département ───
    if len(departments) == 1:
        query_filter = Filter(must=[
            FieldCondition(key="department", match=MatchValue(value=departments[0]))
        ])
        return _search_qdrant(query_vector, top_k, query_filter, kmeans)

    # ─── Multi-départements : recherche par dept + fusion ───
    return _multi_dept_search(query_vector, departments, top_k, kmeans)


def _search_qdrant(query_vector, top_k, query_filter, kmeans):
    """Recherche vectorielle simple dans Qdrant."""
    threshold = 0.2 if kmeans else 0.3
    limit     = top_k * 3 if kmeans else top_k

    result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        with_payload=True,
        score_threshold=threshold,
        query_filter=query_filter
    )

    documents = []
    for point in result.points:
        payload = point.payload
        if payload and "text" in payload:
            documents.append({
                "text":       payload["text"],
                "source":     payload.get("source"),
                "page":       payload.get("page"),
                "department": payload.get("department"),
                "score":      point.score
            })

    documents.sort(key=lambda x: x["score"], reverse=True)

    print(f"\n===== SCORES QDRANT =====")
    for doc in documents[:top_k]:
        print(f"Score: {doc['score']:.3f} | Dept: {doc['department']} | {doc['text'][:100]}")

    return documents[:top_k]


def _multi_dept_search(query_vector, departments: list, top_k: int, kmeans):
    """
    Recherche séparée par département + fusion intelligente.
    Garantit une représentation équitable de chaque département.
    """
    per_dept   = max(2, top_k // len(departments))
    all_docs   = []
    seen_texts = set()

    for dept in departments:
        query_filter = Filter(must=[
            FieldCondition(key="department", match=MatchValue(value=dept))
        ])

        result = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=per_dept * 3,
            with_payload=True,
            score_threshold=0.2,
            query_filter=query_filter
        )

        dept_docs = []
        for point in result.points:
            payload = point.payload
            if not payload or "text" not in payload:
                continue

            # Déduplication
            text_key = payload["text"][:80]
            if text_key in seen_texts:
                continue
            seen_texts.add(text_key)

            dept_docs.append({
                "text":       payload["text"],
                "source":     payload.get("source"),
                "page":       payload.get("page"),
                "department": payload.get("department", dept),
                "score":      point.score
            })

        dept_docs.sort(key=lambda x: x["score"], reverse=True)

        print(f"📂 Dept [{dept}]: {len(dept_docs)} docs trouvés")
        all_docs.extend(dept_docs[:per_dept])

    # Tri global par score
    all_docs.sort(key=lambda x: x["score"], reverse=True)

    print(f"\n===== FUSION MULTI-DEPT =====")
    for doc in all_docs[:top_k]:
        print(f"Score: {doc['score']:.3f} | Dept: {doc['department']} | {doc['text'][:100]}")

    return all_docs[:top_k]