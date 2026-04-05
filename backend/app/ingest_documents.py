# app/ingest_documents.py

import os
from app.services.document_service import create_collection, add_document
from app.utils.pdf_loader import load_all_pdfs_from_folder


def ingest_documents():
    print("🚀 Début ingestion des documents...\n")

    # 1) créer collection Qdrant si elle n'existe pas
    create_collection()

    # 2) chemin du dossier data
    base_dir = os.path.dirname(os.path.dirname(__file__))  # backend/
    data_folder = os.path.join(base_dir, "data")

    print(f"📂 Dossier analysé: {data_folder}\n")

    # 3) charger les PDFs
    chunks = load_all_pdfs_from_folder(data_folder)

    if not chunks:
        print("❌ Aucun chunk à injecter.")
        return

    print(f"\n📦 Total chunks à injecter: {len(chunks)}\n")

    # 4) injecter dans Qdrant
    success = 0
    failed = 0

    for i, item in enumerate(chunks, start=1):
        try:
            add_document(item["text"], item["metadata"])
            success += 1
            print(f"✅ Chunk {i}/{len(chunks)} injecté")
        except Exception as e:
            failed += 1
            print(f"❌ Erreur chunk {i}: {e}")

    print("\n==============================")
    print("🎉 INGESTION TERMINÉE")
    print(f"✅ Succès: {success}")
    print(f"❌ Échecs: {failed}")
    print("==============================\n")


if __name__ == "__main__":
    ingest_documents()