from app.rag.retriever import retrieve_documents
from app.services.llm_service import generate_answer


# 🔹 1️⃣ Détection intelligente des salutations
def is_greeting(text: str) -> bool:
    greetings = [
        "bonjour", "salut", "hello", "hi",
        "hey", "good morning", "good evening",
        "salam", "salem", "السلام عليكم"
    ]

    text_clean = text.strip().lower()

    return any(text_clean.startswith(g) for g in greetings)


# 🔹 2️⃣ Détection simple de langue
def detect_language(text: str):
    text = text.lower()
    english_words = ["the", "who", "what", "how", "is", "are", "why"]
    if any(word in text for word in english_words):
        return "en"
    return "fr"


# 🔹 3️⃣ Construction du prompt
def build_prompt(context_chunks, question):
    context = "\n\n".join(context_chunks)

    return f"""
You are a smart and professional enterprise assistant.

STRICT RULES:
1. Detect the language of the user question.
2. If the question is in French, answer ONLY in French.
3. If the question is in English, answer ONLY in English.
4. Never mix languages.
5. Write one short, clear paragraph (maximum 4 sentences).
6. Reformulate naturally.
7. Do not repeat ideas.
8. Do not create lists.
9. Do not invent information.

IMPORTANT:
- Use only the information from the context.
- If the answer is not found in the context, say you cannot find it.

CONTEXT:
{context}

QUESTION:
{question}

FINAL ANSWER:
"""


# 🔹 4️⃣ Pipeline principal
def run_pipeline(question: str):

    question = question.strip()

    # ✅ Gestion salutations
    if is_greeting(question):

        if question.lower().startswith(("hello", "hi", "hey", "good","yoo","morning","good morning")):
            answer = "Hello 👋 I'm your enterprise AI assistant. How can I help you today?"
        else:
            answer = "Bonjour 👋 Je suis votre assistant IA entreprise. Comment puis-je vous aider aujourd’hui ?"

        return {
            "question": question,
            "answer": answer,
            "sources": []
        }

    # 🔎 Détection langue
    lang = detect_language(question)

    # 🔎 Recherche documents
    documents = retrieve_documents(question)

    # ❌ Aucun document trouvé
    if not documents:

        if lang == "en":
            answer = "I cannot find the requested information in the available documents."
        else:
            answer = "Je ne trouve pas l'information dans les documents disponibles."

        return {
            "question": question,
            "answer": answer,
            "sources": []
        }

    # 🧠 Construction prompt
    prompt = build_prompt(documents, question)

    # 🤖 Génération réponse principale
    answer = generate_answer(prompt)

    # 🔁 Reformulation propre en anglais si nécessaire
    if lang == "en":
        translation_prompt = f"""
Rewrite this answer clearly and naturally in English.
Do not change the meaning.

Answer:
{answer}
"""
        answer = generate_answer(translation_prompt)

    return {
        "question": question,
        "answer": answer,
        "sources": documents
    }
