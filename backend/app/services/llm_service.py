import requests
from app.core.config import OLLAMA_URL, LLM_MODEL


def generate_answer(prompt: str):
    try:
        response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )





        response.raise_for_status()

        return response.json()["response"]

    except requests.exceptions.RequestException as e:
        return f"Erreur Ollama: {str(e)}"
