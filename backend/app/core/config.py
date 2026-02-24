import os

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = 6333

COLLECTION_NAME = "enterprise_documents"

EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL = "qwen:1.8b" 

VECTOR_SIZE = 768