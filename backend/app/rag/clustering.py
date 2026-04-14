import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from typing import List, Dict
import pickle
import os

CLUSTERS_FILE = "/app/data/kmeans_model.pkl"
CENTROIDS_FILE = "/app/data/kmeans_centroids.npy"


def train_kmeans(vectors: List[List[float]], n_clusters: int = 10) -> KMeans:
    """
    Entraîne un modèle K-Means sur les vecteurs des documents.
    """
    X = np.array(vectors)
    X = normalize(X)  # normalisation cosine

    # ✅ Ajuster n_clusters si moins de documents
    n_clusters = min(n_clusters, len(X))

    print(f"🔄 Entraînement K-Means avec {n_clusters} clusters sur {len(X)} vecteurs...")

    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10,
        max_iter=300
    )
    kmeans.fit(X)

    # ✅ Sauvegarder le modèle
    os.makedirs("/app/data", exist_ok=True)
    with open(CLUSTERS_FILE, "wb") as f:
        pickle.dump(kmeans, f)
    np.save(CENTROIDS_FILE, kmeans.cluster_centers_)

    print(f"✅ K-Means entraîné — {n_clusters} clusters sauvegardés")
    return kmeans


def load_kmeans() -> KMeans:
    """Charge le modèle K-Means existant."""
    if not os.path.exists(CLUSTERS_FILE):
        return None
    with open(CLUSTERS_FILE, "rb") as f:
        return pickle.load(f)


def get_best_clusters(query_vector: List[float], kmeans: KMeans, top_k: int = 3) -> List[int]:
    """
    Trouve les clusters les plus proches de la question.
    Retourne les indices des top_k clusters les plus pertinents.
    """
    q = np.array(query_vector).reshape(1, -1)
    q = normalize(q)

    # Distance aux centroïdes
    distances = kmeans.transform(q)[0]

    # Trier par distance croissante (plus proche = plus pertinent)
    best_clusters = np.argsort(distances)[:top_k].tolist()

    print(f"🎯 Clusters sélectionnés : {best_clusters} (distances: {distances[best_clusters].round(3)})")
    return best_clusters


def assign_cluster(vector: List[float], kmeans: KMeans) -> int:
    """Assigne un cluster à un vecteur."""
    v = np.array(vector).reshape(1, -1)
    v = normalize(v)
    return int(kmeans.predict(v)[0])