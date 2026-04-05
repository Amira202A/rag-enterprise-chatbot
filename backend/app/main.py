from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time

from app.services.document_service import create_collection
from app.api.chat import router as chat_router
from app.api.conversation import router as conversation_router
from app.api.auth import router as auth_router
from app.database.sql import engine, Base
from app.models.user import User  # nécessaire pour créer la table

app = FastAPI(
    title="RAG Enterprise Chatbot",
    description="Backend RAG avec Qdrant + Ollama + Auth",
    version="2.0.0"
)

# ✅ CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.on_event("startup")
def startup_event():
    print("🔄 Initialisation du backend...")
    for i in range(10):
        try:
            print(f"🔁 Tentative {i+1}/10...")
            create_collection()
            Base.metadata.create_all(bind=engine)
            print("✅ Backend prêt (RAG + Auth).")
            break
        except Exception as e:
            print("⏳ Attente des services...")
            print("Erreur :", e)
            time.sleep(3)
    else:
        print("❌ Impossible de démarrer après plusieurs tentatives.")

# ✅ ROUTERS
app.include_router(chat_router)
app.include_router(conversation_router)
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "Backend RAG + Auth fonctionne 🚀"}