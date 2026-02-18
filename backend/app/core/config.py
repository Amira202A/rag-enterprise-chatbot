import os

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

COLLECTION_NAME = "enterprise_documents"

EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_URL = "http://127.0.0.1:11434"
LLM_MODEL = "llama3.2:1b"






VECTOR_SIZE = 768
