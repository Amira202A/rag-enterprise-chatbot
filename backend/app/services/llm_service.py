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
                    "num_predict": 50,     # réponse un peu plus complète
                    "temperature": 0.1,
                    "top_k": 10,
                    "num_ctx": 384,        # 🔥 réduit = plus rapide
                   
                }
            },
            timeout=60   # 🔥 MAX 60 sec
        )

        response.raise_for_status()

        result = response.json()["response"]

        print("⏱ LLM réel:", time.time() - start)

        return result

    except requests.exceptions.Timeout:
        return "⚠️ The model is taking too long to respond."

    except Exception as e:
        return f"⚠️ Error: {str(e)}"