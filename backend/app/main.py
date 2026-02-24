from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.document_service import create_collection
from app.api.chat import router as chat_router


app = FastAPI(
    title="RAG Enterprise Chatbot",
    description="Backend RAG avec Qdrant + Ollama",
    version="1.0.0"
)

# ✅ Ajout du CORS pour Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # frontend Angular
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Création automatique de la collection au démarrage
@app.on_event("startup")
def startup_event():
    print("🔄 Initialisation du backend...")
    create_collection()
    print("✅ Backend prêt.")



app.include_router(chat_router)



@app.get("/")
def root():
    return {
        "message": "Backend RAG fonctionne 🚀"
    }
