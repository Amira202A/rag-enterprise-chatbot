from pypdf import PdfReader
from app.services.document_service import add_document, create_collection

# ✅ MODIFICATION: ajout department pour chaque PDF
PDF_FILES = [
    {"path": "data/fichier1.pdf", "department": "IT"},
    {"path": "data/ml.pdf", "department": "IT"},
    # {"path": "data/rh.pdf", "department": "RH"},
    # {"path": "data/marketing.pdf", "department": "Marketing"},
]


def chunk_text(text, chunk_size=600, overlap=80):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if len(chunk) > 50:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# ✅ MODIFICATION: ajout param department
def ingest_pdf(path, department=None):
    print(f"\n📄 Lecture du PDF : {path} | Département: {department}")
    reader = PdfReader(path)
    total_chunks = 0
    seen_chunks = set()

    for page_number, page in enumerate(reader.pages):

        if page_number < 2:
            continue

        text = page.extract_text()
        if not text or len(text.strip()) < 30:
            continue

        chunks = chunk_text(text)

        for chunk in chunks:
            chunk_hash = hash(chunk[:100])
            if chunk_hash in seen_chunks:
                continue
            seen_chunks.add(chunk_hash)

            add_document(
                chunk,
                metadata={
                    "source": path.split("/")[-1],
                    "page": page_number + 1,
                    "department": department  # ✅ ajouté
                }
            )
            total_chunks += 1

    print(f"✅ {path} ingéré — {total_chunks} chunks ajoutés pour {department}")


def main():
    print("🚀 Début ingestion")
    create_collection()

    # ✅ MODIFICATION: boucle avec department
    for pdf in PDF_FILES:
        ingest_pdf(pdf["path"], department=pdf["department"])

    print("🎉 Ingestion terminée")


if __name__ == "__main__":
    main()