from app.rag.retriever import retrieve_documents
from app.services.llm_service import generate_answer
from app.nlp.tunisian_detector import is_tunisian_arabizi
from app.nlp.tunisian_normalizer import normalize_tunisian
from app.nlp.intent_detector import detect_intent
import time


# ─────────────── CONTEXTE PAR DÉPARTEMENT ───────────────
DEPT_CONTEXT = {
    "IT": {
        "role": "expert en informatique, infrastructure et cybersécurité",
        "topics": "support technique, infrastructure réseau, cybersécurité, "
                  "maintenance systèmes, logiciels internes, documentation technique",
        "lang": "technique et précis"
    },
    "RH": {
        "role": "expert en ressources humaines",
        "topics": "congés, recrutement, paie, règlements internes, "
                  "assurances, contrats, gestion administrative",
        "lang": "professionnel et bienveillant"
    },
    "Finance": {
        "role": "expert financier et comptable",
        "topics": "factures, budgets, comptabilité, dépenses, "
                  "rapports financiers, trésorerie",
        "lang": "précis et chiffré"
    },
    "Marketing": {
        "role": "expert en marketing et communication",
        "topics": "campagnes marketing, stratégie de communication, "
                  "réseaux sociaux, analyse de marché, branding",
        "lang": "créatif et orienté résultats"
    },
    "Direction": {
        "role": "assistant de direction",
        "topics": "stratégie d'entreprise, rapports de direction, "
                  "décisions managériales, gouvernance",
        "lang": "stratégique et synthétique"
    }
}


# ─────────────── DÉTECTION LANGUE ───────────────
def detect_language(text: str) -> str:
    """Détecte la langue de la question."""
    text_lower = text.lower()

    # Tunisien Arabizi (priorité)
    if is_tunisian_arabizi(text):
        return "tunisian"

    # Arabe standard
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    if arabic_chars > len(text) * 0.3:
        return "arabic"

    # Anglais
    english_words = [
        "what", "who", "where", "when", "how", "why", "which",
        "is", "are", "the", "give", "tell", "define", "explain",
        "can", "could", "would", "should", "does", "do", "did",
        "a", "an", "of", "in", "for", "to", "and", "with"
    ]
    english_score = sum(1 for w in text_lower.split() if w in english_words)
    if english_score >= 1:
        return "english"

    # Français
    french_words = [
        "qu", "est", "une", "des", "les", "que", "qui", "comment",
        "pourquoi", "quoi", "quel", "quelle", "definition", "définition",
        "donne", "explique", "parle", "je", "tu", "il", "nous", "vous",
        "de", "du", "au", "aux", "sur", "dans", "avec", "pour", "par"
    ]
    french_score = sum(1 for w in text_lower.split() if w in french_words)
    if french_score >= 1:
        return "french"

    return "french"  # défaut


# ─────────────── CONTEXTE DÉPARTEMENT ───────────────
def get_dept_context(departments: list) -> dict:
    """Retourne le contexte combiné pour un ou plusieurs départements."""
    if not departments:
        return {
            "role":   "assistant IA d'entreprise",
            "topics": "informations générales de l'entreprise",
            "lang":   "professionnel"
        }

    if len(departments) == 1:
        dept = departments[0]
        return DEPT_CONTEXT.get(dept, {
            "role":   f"expert du département {dept}",
            "topics": f"informations liées au département {dept}",
            "lang":   "professionnel"
        })

    roles  = []
    topics = []
    for dept in departments:
        ctx = DEPT_CONTEXT.get(dept)
        if ctx:
            roles.append(ctx["role"])
            topics.append(ctx["topics"])

    return {
        "role":   " et ".join(roles) if roles else "assistant IA d'entreprise",
        "topics": ", ".join(topics)  if topics else "informations de l'entreprise",
        "lang":   "professionnel et complet"
    }


# ─────────────── PROMPT BUILDER ───────────────
def build_prompt(context_chunks, question, departments=None, is_tunisian=False, language="french"):
    context    = "\n\n".join(context_chunks)
    dept_names = ", ".join(departments) if departments else "tous les départements"

    if language == "tunisian":
        return f"""Contexte:
{context}

Question: {question}

Ijeb BASS mel contexte. La tjawb men 3endek.
Ken ma3louma mawjoudach: "Ma nal9ach el ma3louma hedhi fel documents eli 3andi."
Ijeb bel tunsi arabizi.

Jaweb:"""

    if language == "arabic":
        return f"""السياق:
{context}

السؤال: {question}

أجب فقط باستخدام السياق أعلاه.
إذا لم تجد المعلومات قل: "لا أجد هذه المعلومات في وثائق قسمك."
أجب باللغة العربية.

الإجابة:"""

    if language == "english":
        return f"""Context:
{context}

Question: {question}

Answer ONLY using the context above.
If not found, say: "I cannot find this information in your department's documents ({dept_names})."
Answer in English.

Answer:"""

    # Français (défaut)
    return f"""Contexte:
{context}

Question: {question}

Réponds UNIQUEMENT en utilisant le contexte ci-dessus.
Si l'information n'est pas trouvée, dis: "Je ne trouve pas cette information dans les documents du département {dept_names}."
Réponds en français.

Réponse:"""


# ─────────────── FILTRAGE DOCS ───────────────
def filter_relevant_docs(documents, question, departments=None, is_admin=False):
    """Filtre strict par département + scoring de pertinence."""

    if is_admin:
        filtered      = documents
        access_denied = False
    else:
        filtered    = []
        denied_docs = []

        for doc in documents:
            doc_dept = doc.get("department") if isinstance(doc, dict) else None

            if doc_dept and doc_dept in departments:
                filtered.append(doc)
            else:
                denied_docs.append(doc)

        access_denied = len(filtered) == 0 and len(denied_docs) > 0

    if not filtered:
        return [], access_denied

    question_words = [w for w in question.lower().split() if len(w) > 2]

    scored = []
    for doc in filtered:
        text  = doc["text"].lower() if isinstance(doc, dict) else doc.lower()
        score = sum(word in text for word in question_words)
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored], False


# ─────────────── RÉPONSES RAPIDES ───────────────
def quick_response(intent, original_question, is_tunisian=False, departments=None, language="french"):
    dept_info = f" spécialisé en {', '.join(departments)}" if departments else ""
    topics    = get_dept_context(departments)["topics"] if departments else "les informations de l'entreprise"
    dept_str  = ', '.join(departments) if departments else 'votre entreprise'

    if intent == "greeting":
        if language == "tunisian":
            return f"3aslema 👋 Ena assistant IA mte3ek. Kifeh n9dar n3awnek ?"
        if language == "english":
            return f"Hello 👋 I'm your enterprise AI assistant{dept_info}. How can I help you?"
        if language == "arabic":
            return f"مرحبا 👋 أنا مساعدك الذكي. كيف يمكنني مساعدتك؟"
        return f"Bonjour 👋 Je suis votre assistant IA{dept_info}. Comment puis-je vous aider ?"

    if intent == "wellbeing":
        if language == "tunisian": return "Labes 😊 W enti ?"
        if language == "english":  return "I'm doing great 😊 And you?"
        if language == "arabic":   return "بخير 😊 وأنت؟"
        return "Ça va bien 😊 Et vous ?"

    if intent == "help":
        if language == "tunisian": return f"Bien sûr 😊 N9dar n3awnek fi : {dept_str}."
        if language == "english":  return f"Of course 😊 I can help you with: {dept_str}."
        if language == "arabic":   return f"بالتأكيد 😊 يمكنني مساعدتك في: {dept_str}."
        return f"Bien sûr 😊 Je suis là pour vous aider sur : {dept_str}."

    if intent == "capabilities":
        if language == "tunisian": return f"N9dar njawbek 3la : {topics}."
        if language == "english":  return f"I can answer questions about: {topics}."
        if language == "arabic":   return f"يمكنني الإجابة على أسئلة حول: {topics}."
        return f"Je peux répondre à vos questions sur : {topics}."

    if intent == "casual_reply":
        if language == "tunisian": return "Behi 😊 Ech tħeb t3arf ?"
        if language == "english":  return "Got it 😊 What would you like to know?"
        if language == "arabic":   return "حسنًا 😊 ماذا تريد أن تعرف؟"
        return "D'accord 😊 Comment puis-je vous aider ?"

    return None


# ─────────────── QUERY FAIBLE ───────────────
def is_weak_query(text):
    weak  = {"ok", "merci", "thanks", "behi", "oui", "yes"}
    words = text.lower().strip().split()
    return len(words) <= 2 and all(w in weak or len(w) <= 3 for w in words)


# ─────────────── CONTEXTE MULTI-DÉPARTEMENT ───────────────
def _build_multidept_context(documents, departments):
    """Construit un contexte structuré par département."""
    dept_chunks = {dept: [] for dept in departments}

    for doc in documents:
        dept = doc.get("department") if isinstance(doc, dict) else None
        text = doc["text"]          if isinstance(doc, dict) else doc
        if dept and dept in dept_chunks:
            dept_chunks[dept].append(text)

    context_parts = []
    for dept, chunks in dept_chunks.items():
        if chunks:
            context_parts.append(
                f"=== {dept.upper()} ===\n" + "\n".join(chunks[:2])
            )

    return context_parts if context_parts else [
        doc["text"] if isinstance(doc, dict) else doc
        for doc in documents[:4]
    ]


# ─────────────── PIPELINE PRINCIPAL ───────────────
def run_pipeline(question: str, departments: list = None, is_admin: bool = False):

    question    = question.strip()
    total_start = time.time()

    tunisian_mode       = is_tunisian_arabizi(question)
    normalized_question = normalize_tunisian(question)
    intent              = detect_intent(normalized_question)
    language            = detect_language(question)

    print("\n===== PIPELINE DEBUG =====")
    print(f"Question     : {question}")
    print(f"Départements : {departments}")
    print(f"Admin        : {is_admin}")
    print(f"Intent       : {intent}")
    print(f"Tunisian     : {tunisian_mode}")
    print(f"Langue       : {language}")

    # ─── Blocage sans département ───
    if not is_admin and (not departments or len(departments) == 0):
        if language == "english":
            return {"question": question, "answer": "🔒 You have no department access. Please contact your administrator.", "sources": []}
        if language == "arabic":
            return {"question": question, "answer": "🔒 ليس لديك صلاحية الوصول إلى أي قسم. تواصل مع المسؤول.", "sources": []}
        if language == "tunisian":
            return {"question": question, "answer": "🔒 Ma3andekch access. Kellem l'administrateur.", "sources": []}
        return {"question": question, "answer": "🔒 Vous n'avez accès à aucun département. Contactez votre administrateur.", "sources": []}

    # ─── Réponses rapides ───
    fast_answer = quick_response(intent, question, tunisian_mode, departments, language)
    if fast_answer:
        return {"question": question, "answer": fast_answer, "sources": []}

    # ─── Question faible ───
    if is_weak_query(normalized_question):
        if language == "english":  return {"question": question, "answer": "Could you please clarify your question? 😊", "sources": []}
        if language == "arabic":   return {"question": question, "answer": "هل يمكنك توضيح سؤالك؟ 😊", "sources": []}
        if language == "tunisian": return {"question": question, "answer": "Fahem mich mezien. 3awed 9ollha tani 😊", "sources": []}
        return {"question": question, "answer": "Pouvez-vous préciser votre demande ? 😊", "sources": []}

    # ─── Retrieval ───
    try:
        documents = retrieve_documents(
            normalized_question,
            top_k=6,
            departments=None if is_admin else departments
        )
    except Exception as e:
        print(f"❌ Erreur retrieval: {e}")
        documents = []

    print(f"📚 {len(documents)} documents récupérés")

    # ─── Filtrage final ───
    documents, access_denied = filter_relevant_docs(
        documents,
        normalized_question,
        departments=departments,
        is_admin=is_admin
    )

    print(f"✅ {len(documents)} docs après filtrage | access_denied={access_denied}")

    # ─── Accès refusé ───
    if access_denied:
        dept_str = ", ".join(departments) if departments else "votre département"
        if language == "tunisian": return {"question": question, "answer": "🔒 Ma3andekch access l'hatha el ma3louma.", "sources": []}
        if language == "english":  return {"question": question, "answer": f"🔒 You don't have access to this information ({dept_str}).", "sources": []}
        if language == "arabic":   return {"question": question, "answer": f"🔒 ليس لديك صلاحية الوصول لهذه المعلومات.", "sources": []}
        return {"question": question, "answer": f"🔒 Cette information n'est pas accessible pour le département : {dept_str}.", "sources": []}

    # ─── Aucun document ───
    if not documents:
        dept_str = ", ".join(departments) if departments else "votre département"
        if language == "tunisian": return {"question": question, "answer": "Ma l9itech ma3louma fel documents mte3 departmentik.", "sources": []}
        if language == "english":  return {"question": question, "answer": f"I cannot find this information in your department's documents ({dept_str}).", "sources": []}
        if language == "arabic":   return {"question": question, "answer": f"لا أجد هذه المعلومات في وثائق قسمك ({dept_str}).", "sources": []}
        return {"question": question, "answer": f"Je ne trouve pas d'information dans les documents du département : {dept_str}.", "sources": []}

    # ─── Construction du contexte ───
    if departments and len(departments) > 1:
        context_chunks = _build_multidept_context(documents, departments)
    else:
        context_chunks = [
            doc["text"] if isinstance(doc, dict) else doc
            for doc in documents
        ][:4]

    # ─── Vérification pertinence contexte vs question ───
    question_words  = [w for w in normalized_question.lower().split() if len(w) > 3]
    context_text    = " ".join(context_chunks).lower()
    relevance_score = sum(1 for w in question_words if w in context_text)

    print(f"🎯 Pertinence contexte: {relevance_score}/{len(question_words)}")

    if len(question_words) > 0 and relevance_score == 0:
        dept_names = ", ".join(departments) if departments else "votre département"
        if language == "tunisian": return {"question": question, "answer": "Ma nal9ach el ma3louma hedhi fel documents eli 3andi.", "sources": []}
        if language == "english":  return {"question": question, "answer": f"I cannot find this information in your department's documents ({dept_names}).", "sources": []}
        if language == "arabic":   return {"question": question, "answer": f"لا أجد هذه المعلومات في وثائق قسمك ({dept_names}).", "sources": []}
        return {"question": question, "answer": f"Je ne trouve pas cette information dans les documents de votre département ({dept_names}).", "sources": []}

    # ─── Prompt + LLM ───
    prompt = build_prompt(
        context_chunks,
        normalized_question,
        departments=None if is_admin else departments,
        is_tunisian=tunisian_mode,
        language=language
    )

    answer = generate_answer(prompt)

    print(f"⏱ TOTAL: {round(time.time() - total_start, 2)}s")

    return {
        "question": question,
        "answer":   answer,
        "sources":  documents[:4]
    }