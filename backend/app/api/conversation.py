from fastapi import APIRouter, Header, HTTPException
from app.database.mongo import conversations_collection, messages_collection
from datetime import datetime
from bson import ObjectId
import jwt
from app.core.config import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/conversation", tags=["Conversation"])


# ✅ Auth
def get_user_id_from_token(authorization: str = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token manquant")
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Token invalide")


# ✅ Créer une nouvelle conversation
@router.post("/new")
def create_conversation(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)

    conversation = {
        "title": "Nouvelle conversation",
        "created_at": datetime.utcnow(),
        "messages": [],
        "user_id": user_id
    }

    result = conversations_collection.insert_one(conversation)
    return {"conversation_id": str(result.inserted_id)}


# ✅ Ajouter un message
@router.post("/{conversation_id}/message")
def add_message(conversation_id: str, question: str, answer: str):
    message = {
        "question": question,
        "answer": answer,
        "conversationId": ObjectId(conversation_id),
        "created_at": datetime.utcnow()
    }

    result = messages_collection.insert_one(message)

    conversations_collection.update_one(
        {"_id": ObjectId(conversation_id)},
        {"$push": {"messages": result.inserted_id}}
    )

    message_count = messages_collection.count_documents({
        "conversationId": ObjectId(conversation_id)
    })

    if message_count == 1:
        title = question[:40]
        conversations_collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {"title": title}}
        )

    return {
        "message_id": str(result.inserted_id),
        "conversation_id": conversation_id
    }


# ✅ Récupérer conversations (avec messages + user)
@router.get("/full")
def get_conversations(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)

    conversations = []

    for conv in conversations_collection.find({"user_id": user_id}).sort("created_at", -1):
        messages = []
        for msg_id in conv.get("messages", []):
            msg = messages_collection.find_one({"_id": msg_id})
            if msg:
                messages.append({
                    "role": "user",
                    "content": msg["question"],
                    "timestamp": str(msg["created_at"])
                })
                messages.append({
                    "role": "bot",
                    "content": msg["answer"],
                    "timestamp": str(msg["created_at"])
                })

        conversations.append({
            "id": str(conv["_id"]),
            "title": conv.get("title", "Nouvelle conversation"),
            "messages": messages
        })

    return conversations


# ✅ Liste simple (par user)
@router.get("/")
def get_all_conversations(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)

    conversations = list(
        conversations_collection.find({"user_id": user_id}).sort("created_at", -1)
    )

    for conv in conversations:
        conv["_id"] = str(conv["_id"])

    return conversations


# ✅ Détail conversation
@router.get("/{conversation_id}")
def get_conversation_with_messages(conversation_id: str):
    conversation = conversations_collection.find_one(
        {"_id": ObjectId(conversation_id)}
    )

    if not conversation:
        return {"error": "Conversation not found"}

    messages = list(
        messages_collection.find({"conversationId": ObjectId(conversation_id)})
    )

    for msg in messages:
        msg["_id"] = str(msg["_id"])
        msg["conversationId"] = str(msg["conversationId"])

    conversation["_id"] = str(conversation["_id"])
    conversation["messages"] = messages

    return conversation