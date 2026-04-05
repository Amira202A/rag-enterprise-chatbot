from app.rag.retriever import retrieve_documents
from app.services.llm_service import generate_answer
from app.nlp.tunisian_detector import is_tunisian_arabizi
from app.nlp.tunisian_normalizer import normalize_tunisian
from app.nlp.intent_detector import detect_intent
import time


def filter_relevant_docs(documents, question):
    question_words = [
        w for w in question.lower().split()
        if len(w) > 2
    ]

    scored = []

    for doc in documents:
        text = doc["text"].lower() if isinstance(doc, dict) else doc.lower()
        score = sum(word in text for word in question_words)
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        return []

    return [doc for _, doc in scored]


def build_prompt(context_chunks, question, is_tunisian=False):
    context = "\n\n".join(context_chunks)

    if is_tunisian:
        return f"""
You are an enterprise AI assistant.

IMPORTANT RULES:
- Answer ONLY using the provided context.
- If the answer is not explicitly in the context, say EXACTLY:
  "Ma nal9ach el ma3louma hedhi fel documents eli 3andi."
- Do NOT invent information.
- Do NOT use prior knowledge.
- Keep the answer short, clear, and useful.
- If the user writes in Tunisian Arabizi, answer in simple Tunisian Arabizi.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""
    else:
        return f"""
You are a strict enterprise AI assistant.

IMPORTANT RULES:
- Answer ONLY using the provided context.
- If the answer is not explicitly in the context, say EXACTLY:
  "Je ne trouve pas cette information dans les documents disponibles."
- Do NOT use prior knowledge.
- Do NOT guess.
- Keep the answer short (2-4 sentences max).
- Answer in the same language as the user's question when possible.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""


def quick_response(intent: str, original_question: str, is_tunisian: bool = False):
    q = original_question.lower().strip()

    if intent == "greeting":
        if q.startswith(("hello", "hi", "hey", "good")):
            return "Hello 👋 I'm your enterprise AI assistant. How can I help you today?"
        if is_tunisian:
            return "3aslema 👋 Ena assistant IA mte3ek. Kifeh n9dar n3awnek ?"
        return "Bonjour 👋 Je suis votre assistant IA entreprise. Comment puis-je vous aider aujourd’hui ?"

    if intent == "wellbeing":
        if is_tunisian:
            return "Labes الحمدلله 😊 W enti / w enty ?"
        if q in ["cv", "ça va", "ca va"]:
            return "Ça va bien 😊 Et vous ?"
        return "Je vais bien 😊 Et vous ?"

    if intent == "help":
        if is_tunisian:
            return "أكيد 😊 9olli chnowa t7eb ta3ref w ena نحاول n3awnek."
        return "Bien sûr 😊 Dites-moi ce dont vous avez besoin et je vais essayer de vous aider."

    if intent == "ask_ready":
        if is_tunisian:
            return "Ey bien sûr 😊 Tfadhal, es2elni eli t7eb w n7اول n3awnek b akther wodh7."
        return "Bien sûr 😊 Je vous écoute, posez votre question."

    if intent == "capabilities":
        if is_tunisian:
            return "Najem n3awnek fel as2la, nfassarlek ma3loumet, nlawwejlek fel documents, w njewbek 3la 7seb el mawjoud 3andi."
        return "Je peux répondre à vos questions, rechercher dans les documents disponibles et vous aider à retrouver des informations utiles."

    if intent == "casual_reply":
        if is_tunisian:
            return "Mrigel 😊 Ken t7eb, kamel es2elni."
        return "Avec plaisir 😊 Si vous voulez, continuez votre question."

    if intent == "smalltalk":
        if is_tunisian:
            return "Ena assistant IA, w najem n7اول n3awnek 9ad ma najm 😊"
        return "Je suis un assistant IA conçu pour vous aider au mieux 😊"

    return None


def is_weak_query(text: str) -> bool:
    weak_words = {
        "ok", "okay", "merci", "thanks", "thank you",
        "behi", "behy", "s7i7", "ey", "oui", "yes",
        "kifeh", "aleh", "chnowa"
    }

    words = text.lower().strip().split()

    if len(words) <= 2 and all(w in weak_words or len(w) <= 3 for w in words):
        return True

    return False


def run_pipeline(question: str):
    question = question.strip()
    total_start = time.time()

    tunisian_mode = is_tunisian_arabizi(question)
    normalized_question = normalize_tunisian(question)
    intent = detect_intent(normalized_question)

    print("\n===== DEBUG NLP =====")
    print("Question originale :", question)
    print("Question normalisée :", normalized_question)
    print("Tunisian mode :", tunisian_mode)
    print("Intent détectée :", intent)
    print("=====================\n")

    fast_answer = quick_response(intent, question, tunisian_mode)
    if fast_answer:
        return {
            "question": question,
            "answer": fast_answer,
            "sources": []
        }

    if is_weak_query(normalized_question):
        if tunisian_mode:
            return {
                "question": question,
                "answer": "9olli sou2el akther wodh7 😊 Bech n9dar n3awnek khir.",
                "sources": []
            }
        return {
            "question": question,
            "answer": "Pouvez-vous préciser un peu plus votre demande ? 😊",
            "sources": []
        }

    start = time.time()
    try:
        documents = retrieve_documents(normalized_question, top_k=5)
    except TypeError:
        documents = retrieve_documents(normalized_question)

    print(f"📚 {len(documents)} documents récupérés")
    print("⏱ Retrieval:", round(time.time() - start, 2), "sec")

    documents = filter_relevant_docs(documents, normalized_question)

    print("\n===== DOCUMENTS UTILISÉS =====\n")
    for doc in documents[:5]:
        if isinstance(doc, dict):
            print(doc["text"][:400])
            print(f"\nSOURCE: {doc.get('source')} | PAGE: {doc.get('page')}")
        else:
            print(doc[:400])
        print("\n-----------------\n")

    if not documents:
        if tunisian_mode:
            return {
                "question": question,
                "answer": "Ma l9itech ma3louma pertinante fel documents eli 3andi.",
                "sources": []
            }
        return {
            "question": question,
            "answer": "Je ne trouve pas d'information pertinente dans les documents.",
            "sources": []
        }

    context_chunks = [
        doc["text"] if isinstance(doc, dict) else doc
        for doc in documents
    ][:3]

    prompt = build_prompt(context_chunks, normalized_question, tunisian_mode)
    print(f"📝 Prompt envoyé ({len(prompt)} chars)")

    start = time.time()
    answer = generate_answer(prompt)
    print("⏱ LLM:", round(time.time() - start, 2), "sec")
    print("⏱ TOTAL:", round(time.time() - total_start, 2), "sec")

    return {
        "question": question,
        "answer": answer,
        "sources": documents[:3]
    }