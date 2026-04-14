from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
import jwt
import numpy as np

from app.core.config import SECRET_KEY, ALGORITHM, QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME
from app.rag.clustering import train_kmeans, load_kmeans
from app.models.user import User
from app.database.sql import SessionLocal

router = APIRouter(prefix="/clustering", tags=["Clustering"])


def get_admin_from_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token manquant")
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Token invalide")


@router.post("/train")
def train_clustering(
    n_clusters: int = 10,
    department: str = None,
    admin=Depends(get_admin_from_token)
):
    """
    Entraîne K-Means sur tous les documents Qdrant.
    Optionnel : filtrer par département.
    """
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # ✅ Récupérer tous les vecteurs
    print("📥 Récupération des vecteurs depuis Qdrant...")

    query_filter = None
    if department:
        query_filter = Filter(
            must=[FieldCondition(
                key="department",
                match=MatchValue(value=department)
            )]
        )

    result = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=5000,
        with_vectors=True,
        with_payload=True,
        scroll_filter=query_filter
    )

    points = result[0]

    if len(points) < 2:
        raise HTTPException(
            status_code=400,
            detail="Pas assez de documents pour entraîner K-Means (minimum 2)"
        )

    vectors  = [p.vector for p in points]
    payloads = [p.payload for p in points]

    print(f"✅ {len(vectors)} vecteurs récupérés")

    # ✅ Entraîner K-Means
    kmeans = train_kmeans(vectors, n_clusters=min(n_clusters, len(vectors)))

    # ✅ Statistiques par cluster
    cluster_stats = {}
    for i, point in enumerate(points):
        cluster_id = int(kmeans.labels_[i])
        dept       = point.payload.get("department", "Non défini")
        source     = point.payload.get("source", "Inconnu")

        if cluster_id not in cluster_stats:
            cluster_stats[cluster_id] = {
                "count": 0,
                "departments": set(),
                "sources": set()
            }

        cluster_stats[cluster_id]["count"]       += 1
        cluster_stats[cluster_id]["departments"].add(dept)
        cluster_stats[cluster_id]["sources"].add(source)

    # Convertir sets en listes pour JSON
    stats = {
        k: {
            "count":       v["count"],
            "departments": list(v["departments"]),
            "sources":     list(v["sources"])
        }
        for k, v in cluster_stats.items()
    }

    return {
        "message":      f"✅ K-Means entraîné avec {kmeans.n_clusters} clusters",
        "total_docs":   len(vectors),
        "n_clusters":   kmeans.n_clusters,
        "cluster_stats": stats
    }


@router.get("/status")
def clustering_status(admin=Depends(get_admin_from_token)):
    """Vérifie si K-Means est entraîné."""
    kmeans = load_kmeans()
    if not kmeans:
        return {"trained": False, "message": "K-Means non entraîné"}
    return {
        "trained":    True,
        "n_clusters": kmeans.n_clusters,
        "message":    f"K-Means actif avec {kmeans.n_clusters} clusters"
    }