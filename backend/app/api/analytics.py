from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database.sql import SessionLocal
from app.database.mongo import conversations_collection, messages_collection
from app.models.user import User
from app.core.config import SECRET_KEY, ALGORITHM
from datetime import datetime, timedelta
from collections import Counter
import jwt
import re

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_admin_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token manquant")
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Accès admin requis")
    return user


# ─────────────── 1. ÉVOLUTION CONVERSATIONS ───────────────
@router.get("/conversations-evolution")
def conversations_evolution(
    period: str = "week",
    admin=Depends(get_admin_user)
):
    now = datetime.utcnow()

    if period == "day":
        days = 1
        fmt  = "%H:00"
        pipeline = [
            {"$match": {"created_at": {"$gte": now - timedelta(days=1)}}},
            {"$group": {
                "_id": {"$hour": "$created_at"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        labels = [f"{h:02d}:00" for h in range(24)]
        data   = {str(r["_id"]): r["count"]
                  for r in conversations_collection.aggregate(pipeline)}
        return {
            "labels": labels,
            "data":   [data.get(str(h), 0) for h in range(24)]
        }

    elif period == "week":
        start = now - timedelta(days=6)
        pipeline = [
            {"$match": {"created_at": {"$gte": start}}},
            {"$group": {
                "_id": {
                    "year":  {"$year":  "$created_at"},
                    "month": {"$month": "$created_at"},
                    "day":   {"$dayOfMonth": "$created_at"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        results = list(conversations_collection.aggregate(pipeline))
        labels, data = [], []
        for i in range(7):
            d = start + timedelta(days=i)
            labels.append(d.strftime("%a %d/%m"))
            count = next((
                r["count"] for r in results
                if r["_id"]["day"]   == d.day
                and r["_id"]["month"] == d.month
                and r["_id"]["year"]  == d.year
            ), 0)
            data.append(count)
        return {"labels": labels, "data": data}

    else:  # month
        start = now - timedelta(days=29)
        pipeline = [
            {"$match": {"created_at": {"$gte": start}}},
            {"$group": {
                "_id": {
                    "year":  {"$year":  "$created_at"},
                    "month": {"$month": "$created_at"},
                    "day":   {"$dayOfMonth": "$created_at"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        results = list(conversations_collection.aggregate(pipeline))
        labels, data = [], []
        for i in range(30):
            d = start + timedelta(days=i)
            labels.append(d.strftime("%d/%m"))
            count = next((
                r["count"] for r in results
                if r["_id"]["day"]   == d.day
                and r["_id"]["month"] == d.month
                and r["_id"]["year"]  == d.year
            ), 0)
            data.append(count)
        return {"labels": labels, "data": data}


# ─────────────── 2. MESSAGES ÉCHANGÉS ───────────────
@router.get("/messages-stats")
def messages_stats(
    period: str = "week",
    admin=Depends(get_admin_user)
):
    now   = datetime.utcnow()
    start = now - timedelta(days=7 if period == "week" else 30 if period == "month" else 1)

    all_messages = list(messages_collection.find(
        {"created_at": {"$gte": start}},
        {"question": 1, "answer": 1, "created_at": 1}
    ))

    user_count = len(all_messages)
    bot_count  = len([m for m in all_messages if m.get("answer")])

    return {
        "user_messages": user_count,
        "bot_messages":  bot_count,
        "total":         user_count + bot_count
    }


# ─────────────── 3. RÉPARTITION PAR DÉPARTEMENT ───────────────
@router.get("/department-distribution")
def department_distribution(admin=Depends(get_admin_user)):
    all_messages = list(messages_collection.find(
        {}, {"departments": 1}
    ))

    dept_counter = Counter()
    for msg in all_messages:
        depts = msg.get("departments", [])
        if isinstance(depts, list):
            for d in depts:
                if d:
                    dept_counter[d] += 1
        elif isinstance(depts, str) and depts:
            dept_counter[depts] += 1

    if not dept_counter:
        return {"labels": ["Aucune donnée"], "data": [0]}

    labels = list(dept_counter.keys())
    data   = list(dept_counter.values())
    return {"labels": labels, "data": data}


# ─────────────── 4. TOP KEYWORDS ───────────────
@router.get("/top-keywords")
def top_keywords(
    limit: int = 10,
    admin=Depends(get_admin_user)
):
    STOPWORDS = {
        "le", "la", "les", "de", "du", "des", "un", "une",
        "et", "en", "est", "que", "qui", "quoi", "pour",
        "avec", "sur", "dans", "par", "ce", "je", "tu", "il",
        "nous", "vous", "ils", "me", "mon", "ma", "mes", "se",
        "the", "is", "are", "what", "how", "can", "do",
        "moi", "ou", "si", "au", "aux", "plus", "bien"
    }

    all_messages = list(messages_collection.find(
        {}, {"question": 1}
    ))

    word_counter = Counter()
    for msg in all_messages:
        question = msg.get("question", "")
        words    = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', question.lower())
        for w in words:
            if w not in STOPWORDS:
                word_counter[w] += 1

    top = word_counter.most_common(limit)

    if not top:
        return {"labels": ["Aucune donnée"], "data": [0]}

    return {
        "labels": [t[0].capitalize() for t in top],
        "data":   [t[1] for t in top]
    }


# ─────────────── 5. TAUX DE SATISFACTION ───────────────
@router.get("/satisfaction")
def satisfaction_rate(admin=Depends(get_admin_user)):
    total_msgs = messages_collection.count_documents({})
    likes      = messages_collection.count_documents({"feedback": "like"})
    dislikes   = messages_collection.count_documents({"feedback": "dislike"})
    total_fb   = likes + dislikes

    rate = round((likes / total_fb * 100), 1) if total_fb > 0 else 0

    return {
        "likes":    likes,
        "dislikes": dislikes,
        "total_feedback": total_fb,
        "satisfaction_rate": rate,
        "total_messages": total_msgs
    }


# ─────────────── 6. DOCUMENTS RAG ───────────────
@router.get("/rag-documents")
def rag_documents(admin=Depends(get_admin_user)):
    from qdrant_client import QdrantClient
    from app.core.config import QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME

    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        result = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=1000,
            with_payload=True
        )

        source_counter = Counter()
        for point in result[0]:
            source = point.payload.get("source", "Inconnu")
            source_counter[source] += 1

        if not source_counter:
            return {"labels": ["Aucun document"], "data": [0]}

        top = source_counter.most_common(10)
        return {
            "labels": [t[0] for t in top],
            "data":   [t[1] for t in top]
        }
    except:
        return {"labels": ["Erreur Qdrant"], "data": [0]}


# ─────────────── 7. HEATMAP ACTIVITÉ ───────────────
@router.get("/heatmap")
def heatmap_activity(admin=Depends(get_admin_user)):
    now   = datetime.utcnow()
    start = now - timedelta(days=28)

    all_messages = list(messages_collection.find(
        {"created_at": {"$gte": start}},
        {"created_at": 1}
    ))

    # Matrice [7 jours][24 heures]
    matrix = [[0] * 24 for _ in range(7)]

    for msg in all_messages:
        dt  = msg.get("created_at")
        if dt:
            day  = dt.weekday()  # 0=Lundi, 6=Dimanche
            hour = dt.hour
            matrix[day][hour] += 1

    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    return {
        "days":   days,
        "hours":  list(range(24)),
        "matrix": matrix
    }


# ─────────────── 8. TAUX D'ÉCHEC / FALLBACK ───────────────
@router.get("/fallback-rate")
def fallback_rate(admin=Depends(get_admin_user)):
    FALLBACK_PHRASES = [
        "je ne trouve pas",
        "je n'ai pas",
        "je ne peux pas",
        "ma nal9ach",
        "i cannot find",
        "information introuvable",
        "fallback",
        "pas de réponse"
    ]

    total    = messages_collection.count_documents({})
    fallback = 0

    if total > 0:
        all_answers = list(messages_collection.find(
            {}, {"answer": 1}
        ))
        for msg in all_answers:
            answer = (msg.get("answer") or "").lower()
            if any(p in answer for p in FALLBACK_PHRASES):
                fallback += 1

    success_rate  = round((total - fallback) / total * 100, 1) if total > 0 else 0
    fallback_rate = round(fallback / total * 100, 1) if total > 0 else 0

    return {
        "total":         total,
        "success":       total - fallback,
        "fallback":      fallback,
        "success_rate":  success_rate,
        "fallback_rate": fallback_rate
    }


# ─────────────── 9. LANGUE UTILISÉE ───────────────
@router.get("/language-distribution")
def language_distribution(admin=Depends(get_admin_user)):
    all_messages = list(messages_collection.find(
        {}, {"question": 1}
    ))

    lang_counter = Counter()

    for msg in all_messages:
        q = msg.get("question", "")

        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', q))
        total_chars  = len(q.replace(" ", ""))

        if total_chars == 0:
            continue

        if arabic_chars / total_chars > 0.3:
            lang_counter["Arabe"] += 1
        else:
            english_words = ['what','who','how','why','the','is','are','give','tell']
            words = q.lower().split()
            en_score = sum(1 for w in words if w in english_words)

            tunisian_words = ['kifeh','labes','aslema','nheb','3andi','mte3','nal9a']
            arabizi = any(d in q for d in ['2','3','5','7','8','9'])
            tun_score = sum(1 for w in tunisian_words if w in q.lower())

            if tun_score >= 1 or arabizi:
                lang_counter["Tunisien Arabizi"] += 1
            elif en_score >= 1:
                lang_counter["Anglais"] += 1
            else:
                lang_counter["Français"] += 1

    if not lang_counter:
        return {"labels": ["Français"], "data": [100]}

    return {
        "labels": list(lang_counter.keys()),
        "data":   list(lang_counter.values())
    }


# ─────────────── RÉSUMÉ GLOBAL ───────────────
@router.get("/summary")
def summary(admin=Depends(get_admin_user), db: Session = Depends(get_db)):
    now   = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_users       = db.query(User).count()
    active_users      = db.query(User).filter(User.is_active == True).count()
    total_convs       = conversations_collection.count_documents({})
    convs_today       = conversations_collection.count_documents({"created_at": {"$gte": today}})
    total_msgs        = messages_collection.count_documents({})
    msgs_today        = messages_collection.count_documents({"created_at": {"$gte": today}})

    return {
        "total_users":   total_users,
        "active_users":  active_users,
        "total_convs":   total_convs,
        "convs_today":   convs_today,
        "total_msgs":    total_msgs,
        "msgs_today":    msgs_today
    }
