import os

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = 6333

COLLECTION_NAME = "enterprise_documents"

EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL = "qwen:1.8b"   # ✅ était phi3:mini — qwen:1.8b = 2x plus rapide sur CPU

VECTOR_SIZE = 768
# ───────── AUTH ─────────
SECRET_KEY = os.getenv("SECRET_KEY", "change_this_secret_key_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# ───────── EMAIL ─────────
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "ton_email@gmail.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "xxxx xxxx xxxx xxxx")  # mot de passe app Gmail
MAIL_FROM    = os.getenv("MAIL_USERNAME", "ton_email@gmail.com")
MAIL_SERVER  = "smtp.gmail.com"
MAIL_PORT    = 587