import requests
from app.core.config import OLLAMA_URL

EMBED_MODEL = "nomic-embed-text"

def generate_embedding(text: str):

    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={
            "model": EMBED_MODEL,
            "prompt": text
        }
    )

    response.raise_for_status()

    return response.json()["embedding"]