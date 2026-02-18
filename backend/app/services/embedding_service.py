import requests
from app.core.config import EMBEDDING_MODEL, OLLAMA_URL


def generate_embedding(text: str):
    """
    Génère un embedding via Ollama en utilisant le modèle défini dans config.py
    """

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={
                "model": EMBEDDING_MODEL,
                "prompt": text
            },
            timeout=60  # 🔥 évite blocage si Ollama freeze
        )

        response.raise_for_status()

        data = response.json()

        return data["embedding"]

    except requests.exceptions.RequestException as e:
        raise Exception(f"Erreur embedding Ollama: {str(e)}")
