from fastapi import APIRouter, Body, Header
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId
import time
import jwt

from app.services.embedding_service import generate_embedding
from app.services.document_service import add_document, search_documents
from app.rag.pipeline import run_pipeline
from app.database.mongo import conversations_collection, messages_collection
from app.core.config import SECRET_KEY, ALGORITHM


# ✅ Router
router = APIRouter()


# ✅ Model
class ChatRequest(BaseModel):
    question: str
    conversation_id: str


# ✅ NOUVEAU: récupérer user + departments + is_admin depuis token
def get_user_from_token(authorization: str = None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        return {"id": None, "departments": [], "is_admin": False}

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "id":          payload.get("sub"),
            "departments": payload.get("departments", []),
            "is_admin":    payload.get("is_admin", False)
        }
    except:
        return {"id": None, "departments": [], "is_admin": False}


# 🔹 TEST EMBEDDING
@router.get("/test-embedding")
def test_embedding():
    vector = generate_embedding("Bonjour ceci est un test")

    return {
        "vector_size": len(vector),
        "first_values": vector[:5]
    }


# 🔹 ADD DOCUMENT
@router.post("/add-document")
def insert_document(text: str = Body(...)):
    return add_document(text)


# 🔹 SEARCH
@router.post("/search")
def search(query: str = Body(...)):
    return search_documents(query)


# 🔹 CHAT
@router.post("/chat")
async def chat(
    request: ChatRequest,
    authorization: str = Header(None)
):
    start = time.time()

    # ✅ récupération user info depuis token
    user_info   = get_user_from_token(authorization)
    departments = user_info.get("departments", [])
    is_admin    = user_info.get("is_admin", False)

    # ✅ pipeline avec departments + is_admin
    result = run_pipeline(request.question, departments=departments, is_admin=is_admin)

    print("\n===== DEBUG RESULT =====")
    print(result)

    duration = round(time.time() - start, 2)

    # 🔹 extraction réponse
    if isinstance(result, dict):
        answer = result.get("answer", "")
    else:
        answer = str(result)

    print("===== DEBUG ANSWER =====")
    print(answer)
    print("========================\n")

    # 🔹 conversion conversation_id
    conversation_id = ObjectId(request.conversation_id)

    # 🔹 sauvegarde message Mongo
    message = {
        "question":       request.question,
        "answer":         answer,
        "conversationId": conversation_id,
        "created_at":     datetime.utcnow(),
        "response_time":  duration,
        "departments":    departments
    }

    inserted = messages_collection.insert_one(message)

    # 🔹 rattacher message à la conversation
    conversations_collection.update_one(
        {"_id": conversation_id},
        {"$push": {"messages": inserted.inserted_id}}
    )

    # 🔹 mettre à jour le titre si c'est une nouvelle conversation
    conversations_collection.update_one(
        {"_id": conversation_id, "title": "Nouvelle conversation"},
        {"$set": {"title": request.question[:40]}}
    )

    return {
        "answer": answer,
        "time": duration
    }