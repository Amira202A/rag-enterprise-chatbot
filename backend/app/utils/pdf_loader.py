# app/utils/pdf_loader.py

import os
from pypdf import PdfReader


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extrait tout le texte d'un fichier PDF
    """
    text = ""

    try:
        reader = PdfReader(pdf_path)

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    except Exception as e:
        print(f"❌ Erreur lecture PDF {pdf_path}: {e}")

    return text.strip()


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 120):
    """
    Découpe un texte en morceaux (chunks) pour le RAG
    """
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def load_all_pdfs_from_folder(folder_path: str):
    """
    Charge tous les PDF d'un dossier et retourne une liste de chunks avec metadata
    """
    all_chunks = []

    if not os.path.exists(folder_path):
        print(f"❌ Dossier introuvable: {folder_path}")
        return []

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]

    if not files:
        print("⚠️ Aucun PDF trouvé dans le dossier.")
        return []

    for filename in files:
        pdf_path = os.path.join(folder_path, filename)
        print(f"📄 Lecture: {filename}")

        text = extract_text_from_pdf(pdf_path)

        if not text:
            print(f"⚠️ Aucun texte extrait de {filename}")
            continue

        chunks = chunk_text(text)

        print(f"   ➜ {len(chunks)} chunks créés")

        for i, chunk in enumerate(chunks, start=1):
            all_chunks.append({
                "text": chunk,
                "metadata": {
                    "source": filename,
                    "page": i
                }
            })

    return all_chunks