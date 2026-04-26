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
            "num_predict": 150,    # ✅ très court
            "temperature": 0.0,    # ✅ déterministe
            "top_k": 3,
            "top_p": 0.5,
            "num_ctx": 400,        # ✅ très court
            "num_thread": 4,
            "repeat_penalty": 1.5
        },
        "stop": [
            "Question:", "Contexte:", "Réponse:",
            "REGLE", "SYSTEM", "USER", "\n\n\n",
            "goul EXACTEMENT", "Ma tjawbch"
        ]
    },
    timeout=120
)

        response.raise_for_status()
        result = response.json()["response"].strip()

        if not result:
            return "Je ne trouve pas de réponse claire dans les documents."

        print("⏱ LLM RAG réel:", round(time.time() - start, 2), "sec")

        return clean_llm_output(result)

    except requests.exceptions.Timeout:
        return "⚠️ Le modèle met trop de temps à répondre."

    except Exception as e:
        return f"⚠️ Error: {str(e)}"


def generate_smalltalk_answer(question: str, is_tunisian: bool = False):
    start = time.time()

    if is_tunisian:
        prompt = f"""
You are a friendly enterprise AI assistant.

STRICT RULES:
- Reply ONLY in simple Tunisian Arabizi (Facebook Tunisian style).
- Be natural, short, friendly and clear.
- Do NOT answer in MSA Arabic.
- Do NOT mix weird languages.
- Do NOT invent enterprise document information.
- If the user is chatting casually, respond casually.
- Maximum 2 short sentences.

USER MESSAGE:
{question}

ANSWER:
"""
    else:
        prompt = f"""
You are a friendly enterprise AI assistant.

STRICT RULES:
- Reply in the same language as the user (French or English).
- Be short, natural, helpful and conversational.
- Do NOT invent enterprise document information.
- Maximum 2 short sentences.
IMPORTANT:
- Always complete your answer.
- Never stop mid-sentence.

USER MESSAGE:
{question}

ANSWER:
"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 80,
                    "temperature": 0.4,
                    "top_k": 20,
                    "top_p": 0.8,
                    "num_ctx": 512,
                    "num_thread": 4,
                    "repeat_penalty": 1.2
                },
                "stop": ["\n\n", "USER MESSAGE:", "ANSWER:"]
            },
            timeout=60
        )

        response.raise_for_status()
        result = response.json()["response"].strip()

        print("⏱ LLM SmallTalk réel:", round(time.time() - start, 2), "sec")

        return clean_llm_output(result)

    except requests.exceptions.Timeout:
        if is_tunisian:
            return "Smahli 😅 tawelt barcha. 3awed 9olli sou2lek b tari9a ashel."
        return "Désolé 😅 la réponse prend trop de temps. Reformulez votre message."

    except Exception as e:
        return f"⚠️ Error: {str(e)}"


def clean_llm_output(text: str) -> str:
    if not text:
        return "Je n'ai pas pu générer une réponse."

    cleaned = text.strip()

    # Supprimer les préfixes parasites
    bad_prefixes = [
        "answer:", "response:", "assistant:", "bot:",
        "réponse:", "output:", "regle:", "règle:",
        "system:", "context:", "contexte:"
    ]

    lowered = cleaned.lower()
    for prefix in bad_prefixes:
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
            lowered = cleaned.lower()
            break

    # ✅ Supprimer tout ce qui ressemble à une répétition du prompt
    stop_phrases = [
        "goul EXACTEMENT",
        "Ma tjawbch",
        "INTERDICTION",
        "ABSOLUTE RULES",
        "SYSTEM INSTRUCTIONS",
        "NEVER VIOLATE",
        "your ONLY source",
        "DO NOT invent",
        "REGLE:",
        "RÈGLE:",
        "Departments:",
        "USER QUESTION:"
    ]

    for phrase in stop_phrases:
        if phrase in cleaned:
            cleaned = cleaned[:cleaned.index(phrase)].strip()

    # Nettoyer les lignes vides multiples
    lines   = [line.strip() for line in cleaned.split("\n") if line.strip()]
    cleaned = " ".join(lines)

    # Si après nettoyage c'est vide
    if not cleaned:
        return "Je ne trouve pas cette information dans les documents disponibles."

    return cleaned