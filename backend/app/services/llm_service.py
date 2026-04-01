import requests
import time
from app.core.config import OLLAMA_URL, LLM_MODEL


def generate_answer(prompt: str):
    start = time.time()

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 80,
                    "temperature": 0.1,
                    "top_k": 5,
                    "top_p": 0.5,
                    "num_ctx": 256,       # ✅ très réduit
                    "num_thread": 4,
                    "repeat_penalty": 1.3  # ✅ empêche la répétition
                },
                "stop": ["\n\n", "Q:", "Context:"]  # ✅ stoppe après la réponse
            },
            timeout=90
        )

        response.raise_for_status()
        result = response.json()["response"].strip()

        # ✅ si le modèle répète la question → réponse vide détectée
        if not result or result.lower() == prompt.split("Q:")[-1].strip().lower():
            return "Je ne trouve pas de réponse claire dans les documents."

        print(f"⏱ LLM réel: {round(time.time() - start, 2)}s")
        return result

    except requests.exceptions.Timeout:
        return "⚠️ Timeout — modèle trop lent sur CPU."

    except Exception as e:
        return f"⚠️ Erreur: {str(e)}"