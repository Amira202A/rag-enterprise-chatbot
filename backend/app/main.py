from fastapi import FastAPI
from app.services.document_service import create_collection
from app.api.chat import router as chat_router


app = FastAPI(
    title="RAG Enterprise Chatbot",
    description="Backend RAG avec Qdrant + Ollama",
    version="1.0.0"
)


# 🔹 Création automatique de la collection au démarrage
@app.on_event("startup")
def startup_event():
    print("🔄 Initialisation du backend...")
    create_collection()
    print("✅ Backend prêt.")


# 🔹 Inclusion des routes API
app.include_router(chat_router)


# 🔹 Route racine (test rapide)
@app.get("/")
def root():
    return {
        "message": "Backend RAG fonctionne 🚀"
    }
