from fastapi import APIRouter, Header, HTTPException
from app.database.mongo import conversations_collection, messages_collection
from datetime import datetime
from bson import ObjectId
import jwt
from app.core.config import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/conversation", tags=["Conversation"])


def get_user_id_from_token(authorization: str = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token manquant")
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Token invalide")


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


@router.get("/full")
def get_conversations(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    conversations = []
    for conv in conversations_collection.find({"user_id": user_id}).sort("created_at", -1):
        if not conv.get("messages"):
            continue
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


@router.get("/")
def get_all_conversations(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    conversations = list(
        conversations_collection.find({"user_id": user_id}).sort("created_at", -1)
    )
    for conv in conversations:
        conv["_id"] = str(conv["_id"])
    return conversations


@router.get("/{conversation_id}")
def get_conversation_with_messages(conversation_id: str, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)  # ✅ extraire l'utilisateur
    
    conversation = conversations_collection.find_one({
        "_id": ObjectId(conversation_id),
        "user_id": user_id  # ✅ vérifier que ça lui appartient
    })
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation introuvable")  # ✅ pas de fuite d'info
    
    messages = list(messages_collection.find({"conversationId": ObjectId(conversation_id)}))
    for msg in messages:
        msg["_id"] = str(msg["_id"])
        msg["conversationId"] = str(msg["conversationId"])
    
    conversation["_id"] = str(conversation["_id"])
    conversation["messages"] = messages
    return conversation