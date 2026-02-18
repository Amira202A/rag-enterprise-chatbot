from fastapi import APIRouter, Body
from pydantic import BaseModel
from app.services.embedding_service import generate_embedding
from app.services.document_service import add_document, search_documents
from app.rag.pipeline import run_pipeline

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
def chat(request: ChatRequest):
    return run_pipeline(request.question)
