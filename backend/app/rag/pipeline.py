from app.rag.retriever import retrieve_documents
from app.services.llm_service import generate_answer
import time


def is_greeting(text: str) -> bool:
    greetings = [
        "bonjour", "salut", "hello", "hi",
        "hey", "good morning", "good evening",
        "salam", "salem", "السلام عليكم"
    ]
    text_clean = text.strip().lower()
    return any(text_clean.startswith(g) for g in greetings)


def filter_relevant_docs(documents, question):
    """
    ✅ Filtre assoupli — score >= 1 mot commun suffit
    + fallback garanti si aucun match
    """
    question_words = [
        w for w in question.lower().split()
        if len(w) > 3  # ✅ ignore les mots courts (le, la, de, un...)
    ]

    scored = []

    for doc in documents:
        text = doc["text"].lower() if isinstance(doc, dict) else doc.lower()
        score = sum(word in text for word in question_words)
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)

    # ✅ retourne toujours quelque chose — même score 0
    return [doc for _, doc in scored]


def build_prompt(context_chunks, question):
    context = context_chunks[0][:300] if context_chunks else ""

    return f"""<|im_start|>system
You are a helpful assistant. Answer using ONLY the context. If not found, say "I don't know".
<|im_end|>
<|im_start|>user
Context: {context}

Question: {question}
<|im_end|>
<|im_start|>assistant
"""


def run_pipeline(question: str):

    question = question.strip()
    total_start = time.time()

    # ✅ Salutations
    if is_greeting(question):
        if question.lower().startswith(("hello", "hi", "hey", "good")):
            answer = "Hello 👋 I'm your enterprise AI assistant. How can I help you today?"
        else:
            answer = "Bonjour 👋 Je suis votre assistant IA entreprise. Comment puis-je vous aider ?"
        return {"question": question, "answer": answer, "sources": []}

    # 🔎 Retrieval
    try:
        documents = retrieve_documents(question, top_k=5)
    except TypeError:
        documents = retrieve_documents(question)

    print(f"📚 {len(documents)} documents récupérés")

    # 🔥 Filtrage assoupli
    documents = filter_relevant_docs(documents, question)

    # ❌ Aucun document
    if not documents:
        return {
            "question": question,
            "answer": "Je ne trouve pas d'information sur ce sujet dans les documents disponibles.",
            "sources": []
        }

    # 🧠 Prompt
    context_chunks = [
        doc["text"] if isinstance(doc, dict) else doc
        for doc in documents
    ][:3]

    prompt = build_prompt(context_chunks, question)

    print(f"📝 Prompt envoyé ({len(prompt)} chars)")

    # 🤖 LLM
    answer = generate_answer(prompt)

    print(f"⏱ TOTAL pipeline: {round(time.time() - total_start, 2)}s")

    return {
        "question": question,
        "answer": answer,
        "sources": documents[:3]
    }