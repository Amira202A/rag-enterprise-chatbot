from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from app.core.config import (
    QDRANT_HOST,
    QDRANT_PORT,
    COLLECTION_NAME,
    VECTOR_SIZE,
)
from app.services.embedding_service import generate_embedding
import uuid


client = QdrantClient(
    host=QDRANT_HOST,
    port=QDRANT_PORT,
)


def create_collection():
    collections = client.get_collections().collections
    existing = [c.name for c in collections]

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        print("✅ Collection créée")
    else:
        print("ℹ️ Collection déjà existante")


def add_document(text: str, metadata: dict = None):
    """
    Ajoute un document (ou chunk) dans Qdrant
    """
    embedding = generate_embedding(text)

    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding,
        payload={
            "text": text,
            "source": metadata.get("source") if metadata else None,
            "page": metadata.get("page") if metadata else None
        }
    )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[point]
    )

    return {"status": "Document ajouté"}


def search_documents(query: str, limit: int = 3):
    """
    Recherche les documents les plus proches du texte donné
    """
    query_vector = generate_embedding(query)

    search_result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit
    )

    results = []

    for hit in search_result.points:
        results.append({
            "score": hit.score,
            "text": hit.payload.get("text", ""),
            "source": hit.payload.get("source"),
            "page": hit.payload.get("page")
        })

    return results


def count_documents():
    """
    Retourne le nombre total de chunks stockés dans Qdrant
    """
    count = client.count(collection_name=COLLECTION_NAME, exact=True)
    return count.count