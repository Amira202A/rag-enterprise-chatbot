from qdrant_client import QdrantClient

client = QdrantClient(host='localhost', port=6333)

try:
    client.delete_collection('enterprise_documents')
    print('✅ Collection supprimée')
except Exception as e:
    print('⚠️ Erreur ou collection inexistante :', e)