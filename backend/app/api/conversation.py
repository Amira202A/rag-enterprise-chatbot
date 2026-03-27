from fastapi import APIRouter
from app.database.mongo import conversations_collection, messages_collection
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/conversation", tags=["Conversation"])


# ✅ Créer une nouvelle conversation
@router.post("/new")
def create_conversation():

    conversation = {
        "title": "Nouvelle conversation",
        "created_at": datetime.utcnow(),
        "messages": []
    }

    result = conversations_collection.insert_one(conversation)

    return {
        "conversation_id": str(result.inserted_id)
    }


# ✅ Ajouter un message dans une conversation
@router.post("/{conversation_id}/message")
def add_message(conversation_id: str, question: str, answer: str):

    message = {
        "question": question,
        "answer": answer,
        "conversationId": ObjectId(conversation_id),
        "created_at": datetime.utcnow()
    }

    result = messages_collection.insert_one(message)

    # ajouter message dans conversation
    conversations_collection.update_one(
        {"_id": ObjectId(conversation_id)},
        {"$push": {"messages": result.inserted_id}}
    )

    # 🔎 vérifier si c'est le premier message
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


# ✅ Récupérer toutes les conversations (simple)
@router.get("/")
def get_all_conversations():

    conversations = list(conversations_collection.find().sort("created_at", -1))

    for conv in conversations:
        conv["_id"] = str(conv["_id"])

    return conversations


# ⭐ Route optimisée pour Angular (avec messages)
@router.get("/full")
def get_conversations():

    conversations = []

    for conv in conversations_collection.find().sort("created_at", -1):

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


# ✅ Récupérer une conversation avec ses messages
@router.get("/{conversation_id}")
def get_conversation_with_messages(conversation_id: str):

    conversation = conversations_collection.find_one(
        {"_id": ObjectId(conversation_id)}
    )

    if not conversation:
        return {"error": "Conversation not found"}

    messages = list(
        messages_collection.find(
            {"conversationId": ObjectId(conversation_id)}
        )
    )

    for msg in messages:
        msg["_id"] = str(msg["_id"])
        msg["conversationId"] = str(msg["conversationId"])

    conversation["_id"] = str(conversation["_id"])
    conversation["messages"] = messages

    return conversation