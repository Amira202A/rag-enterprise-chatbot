from app.rag.retriever import retrieve_documents
from app.services.llm_service import generate_answer
from app.nlp.tunisian_detector import is_tunisian_arabizi
from app.nlp.tunisian_normalizer import normalize_tunisian
from app.nlp.intent_detector import detect_intent
import time


# ✅ FILTRAGE STRICT + ACCÈS REFUSÉ
def filter_relevant_docs(documents, question, departments=None, is_admin=False):
    """
    Filtre strict par département.
    Retourne :
    - documents filtrés
    - access_denied = True si docs existent mais non accessibles
    """

    if is_admin:
        filtered = documents
        access_denied = False

    else:
        filtered = []
        denied_docs = []

        for doc in documents:
            doc_dept = doc.get("department") if isinstance(doc, dict) else None

            # 🔒 STRICT : doc doit avoir un département ET appartenir au user
            if doc_dept and doc_dept in departments:
                filtered.append(doc)
            else:
                denied_docs.append(doc)

        # 🔥 accès refusé si rien accessible MAIS docs existent
        access_denied = len(filtered) == 0 and len(denied_docs) > 0

    if not filtered:
        return [], access_denied

    # 🔎 SCORE DE PERTINENCE
    question_words = [w for w in question.lower().split() if len(w) > 2]

    scored = []
    for doc in filtered:
        text = doc["text"].lower() if isinstance(doc, dict) else doc.lower()
        score = sum(word in text for word in question_words)
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [doc for _, doc in scored], False


# ✅ PROMPT
def build_prompt(context_chunks, question, is_tunisian=False, departments=None):
    context = "\n\n".join(context_chunks)
    dept_info = f" des départements : {', '.join(departments)}" if departments else ""

    if is_tunisian:
        return f"""You are an enterprise AI assistant{dept_info}.
IMPORTANT:
- Answer ONLY using the provided context.
- If not found, say: "Ma nal9ach el ma3louma hedhi fel documents eli 3andi."

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""
    return f"""You are a strict enterprise AI assistant{dept_info}.
IMPORTANT RULES:
- Answer ONLY using the provided context.
- If not found, say: "Je ne trouve pas cette information dans les documents disponibles."
- Keep the answer short (2-4 sentences max).

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""


# ✅ RÉPONSES RAPIDES
def quick_response(intent, original_question, is_tunisian=False):
    q = original_question.lower().strip()

    if intent == "greeting":
        if is_tunisian:
            return "3aslema 👋 Ena assistant IA mte3ek. Kifeh n9dar n3awnek ?"
        return "Bonjour 👋 Je suis votre assistant IA entreprise. Comment puis-je vous aider ?"

    if intent == "wellbeing":
        if is_tunisian:
            return "Labes 😊 W enti ?"
        return "Ça va bien 😊 Et vous ?"

    if intent == "help":
        return "Bien sûr 😊 Dites-moi ce dont vous avez besoin."

    if intent == "capabilities":
        return "Je peux répondre à vos questions selon les documents de vos départements."

    return None


# ✅ QUESTION FAIBLE
def is_weak_query(text):
    weak = {"ok", "merci", "thanks", "behi", "oui", "yes"}
    words = text.lower().strip().split()
    return len(words) <= 2 and all(w in weak or len(w) <= 3 for w in words)


# ✅ PIPELINE PRINCIPAL
def run_pipeline(question: str, departments: list = None, is_admin: bool = False):

    question = question.strip()
    total_start = time.time()

    tunisian_mode = is_tunisian_arabizi(question)
    normalized_question = normalize_tunisian(question)
    intent = detect_intent(normalized_question)

    print("\n===== DEBUG =====")
    print("Question    :", question)
    print("Départements:", departments)
    print("Admin       :", is_admin)

    # 🔒 BLOQUAGE SI PAS DE DÉPARTEMENT
    if not is_admin and (not departments or len(departments) == 0):
        return {
            "question": question,
            "answer": "🔒 Vous n'avez accès à aucun département.",
            "sources": []
        }

    # ⚡ réponses rapides
    fast_answer = quick_response(intent, question, tunisian_mode)
    if fast_answer:
        return {"question": question, "answer": fast_answer, "sources": []}

    # ❗ question faible
    if is_weak_query(normalized_question):
        return {
            "question": question,
            "answer": "Pouvez-vous préciser votre demande ? 😊",
            "sources": []
        }

    # 🔎 RETRIEVAL
    try:
        documents = retrieve_documents(
            normalized_question,
            top_k=5,
            departments=None if is_admin else departments
        )
    except Exception:
        documents = retrieve_documents(normalized_question)

    print(f"📚 {len(documents)} documents récupérés")

    # 🔒 FILTRAGE FINAL
    documents, access_denied = filter_relevant_docs(
        documents,
        normalized_question,
        departments=departments,
        is_admin=is_admin
    )

    print(f"✅ {len(documents)} docs | access_denied={access_denied}")

    # 🔒 CAS ACCÈS REFUSÉ
    if access_denied:
        if tunisian_mode:
            return {
                "question": question,
                "answer": "🔒 Ma3andekch access l'hatha el ma3louma.",
                "sources": []
            }
        return {
            "question": question,
            "answer": "🔒 Vous n'avez pas accès à cette information.",
            "sources": []
        }

    # ❌ aucun document
    if not documents:
        if tunisian_mode:
            return {
                "question": question,
                "answer": "Ma l9itech ma3louma fel documents mte3 departmentik.",
                "sources": []
            }
        return {
            "question": question,
            "answer": "Je ne trouve pas d'information dans les documents de vos départements.",
            "sources": []
        }

    # 🧠 LLM
    context_chunks = [
        doc["text"] if isinstance(doc, dict) else doc
        for doc in documents
    ][:3]

    prompt = build_prompt(
        context_chunks,
        normalized_question,
        tunisian_mode,
        departments
    )

    answer = generate_answer(prompt)

    print(f"⏱ TOTAL: {round(time.time() - total_start, 2)}s")

    return {
        "question": question,
        "answer": answer,
        "sources": documents[:3]
    }