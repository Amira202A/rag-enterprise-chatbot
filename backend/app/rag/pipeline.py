from app.rag.retriever import retrieve_documents
from app.services.llm_service import generate_answer
import time


# 🔹 Détection des salutations
def is_greeting(text: str) -> bool:
    greetings = [
        "bonjour", "salut", "hello", "hi",
        "hey", "good morning", "good evening",
        "salam", "salem", "السلام عليكم"
    ]

    text_clean = text.strip().lower()
    return any(text_clean.startswith(g) for g in greetings)


# 🔥 FILTRAGE INTELLIGENT
def filter_relevant_docs(documents, question):
    question_words = question.lower().split()

    filtered = []

    for doc in documents:
        text = doc["text"].lower() if isinstance(doc, dict) else doc.lower()

        # score = nombre de mots en commun
        score = sum(word in text for word in question_words)

        if score >= 2:
            filtered.append((score, doc))

    # trier par score (plus pertinent en premier)
    filtered.sort(key=lambda x: x[0], reverse=True)

    # fallback
    if not filtered:
        return documents

    return [doc for _, doc in filtered]


# 🔹 Construction du prompt
def build_prompt(context_chunks, question):

    context = "\n\n".join(context_chunks)

    return f"""
You are a strict enterprise AI assistant.

IMPORTANT RULES:
- Answer ONLY using the provided context.
- If the answer is not explicitly in the context, say EXACTLY:
  "I don't know based on the provided documents."
- Do NOT use prior knowledge.
- Do NOT guess.
- Keep the answer short (2-3 sentences max).

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""


# 🔹 Pipeline principal
def run_pipeline(question: str):

    question = question.strip()
    total_start = time.time()

    # ✅ Gestion salutations
    if is_greeting(question):

        if question.lower().startswith(("hello", "hi", "hey", "good")):
            answer = "Hello 👋 I'm your enterprise AI assistant. How can I help you today?"
        else:
            answer = "Bonjour 👋 Je suis votre assistant IA entreprise. Comment puis-je vous aider aujourd’hui ?"

        return {
            "question": question,
            "answer": answer,
            "sources": []
        }

    # 🔎 RETRIEVAL
    start = time.time()

    try:
        documents = retrieve_documents(question, top_k=5)
    except TypeError:
        documents = retrieve_documents(question)

    print("⏱ Retrieval:", time.time() - start)

    # 🔥 FILTRAGE
    documents = filter_relevant_docs(documents, question)

    # 📚 DEBUG
    print("\n===== DOCUMENTS UTILISÉS =====\n")

    for doc in documents:
        if isinstance(doc, dict):
            print(doc["text"][:400])
            print(f"\nSOURCE: {doc.get('source')} | PAGE: {doc.get('page')}")
        else:
            print(doc[:400])

        print("\n-----------------\n")

    # ❌ Aucun document trouvé
    if not documents:
        return {
            "question": question,
            "answer": "Je ne trouve pas d'information pertinente dans les documents.",
            "sources": []
        }

    # 🧠 Construction du prompt
    start = time.time()

    context_chunks = [
        doc["text"] if isinstance(doc, dict) else doc
        for doc in documents
    ][:3]

    prompt = build_prompt(context_chunks, question)

    print("⏱ Prompt:", time.time() - start)

    # 🤖 LLM
    start = time.time()
    answer = generate_answer(prompt)
    print("⏱ LLM:", time.time() - start)

    print("⏱ TOTAL:", time.time() - total_start)

    return {
        "question": question,
        "answer": answer,
        "sources": documents[:3]
    }