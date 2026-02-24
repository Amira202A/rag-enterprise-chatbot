from fastapi import APIRouter, Body
from pydantic import BaseModel
from datetime import datetime

from app.services.embedding_service import generate_embedding
from app.services.document_service import add_document, search_documents
from app.rag.pipeline import run_pipeline

# 🔥 Import Mongo
from database.mongo import collection

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


@router.get("/test-embedding")
def test_embedding():

    vector = generate_embedding("Bonjour ceci est un test")

    return {
        "vector_size": len(vector),
        "first_values": vector[:5]
    }


@router.post("/add-document")
def insert_document(text: str = Body(...)):
    return add_document(text)


@router.post("/search")
def search(query: str = Body(...)):
    return search_documents(query)


@router.post("/chat")
async def chat(request: ChatRequest):

    # 🔹 Exécute ton pipeline RAG
    result = run_pipeline(request.question)

    # Selon ton pipeline, adapte si besoin
    answer = result.get("response") if isinstance(result, dict) else result

    # 🔥 Sauvegarde MongoDB
    collection.insert_one({
        "question": request.question,
        "answer": answer,
        "timestamp": datetime.utcnow()
    })

    return {"response": answer}