# test_search.py  — mets ce fichier dans backend/
import sys
sys.path.insert(0, ".")

from app.services.embedding_service import generate_embedding
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

def test_search(query):
    print(f"\n🔍 Recherche: '{query}'")
    vector = generate_embedding(query)
    
    # sans seuil pour voir TOUS les scores
    result = client.query_points(
        collection_name="enterprise_documents",
        query=vector,
        limit=5,
        with_payload=True
        # pas de score_threshold ici
    )
    
    if not result.points:
        print("❌ Aucun document dans Qdrant !")
        return
        
    for p in result.points:
        print(f"\nScore: {p.score:.3f}")
        print(f"Source: {p.payload.get('source')} | Page: {p.payload.get('page')}")
        print(f"Texte: {p.payload['text'][:200]}")
        print("-" * 40)

test_search("cybercrime")
test_search("machine learning")
test_search("sécurité informatique")