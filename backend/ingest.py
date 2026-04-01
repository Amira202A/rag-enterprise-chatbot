from pypdf import PdfReader
from app.services.document_service import add_document, create_collection

PDF_FILES = [
    "data/fichier1.pdf",
    "data/ml.pdf"
]

def chunk_text(text, chunk_size=600, overlap=80):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if len(chunk) > 50:  # ✅ ignore les chunks trop courts
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def ingest_pdf(path):
    print(f"\n📄 Lecture du PDF : {path}")
    reader = PdfReader(path)
    total_chunks = 0
    seen_chunks = set()  # ✅ déduplication

    for page_number, page in enumerate(reader.pages):

        if page_number < 2:  # ✅ était 5, trop restrictif
            continue

        text = page.extract_text()
        if not text or len(text.strip()) < 30:
            continue

        chunks = chunk_text(text)

        for chunk in chunks:
            # ✅ évite les doublons
            chunk_hash = hash(chunk[:100])
            if chunk_hash in seen_chunks:
                continue
            seen_chunks.add(chunk_hash)

            add_document(
                chunk,
                metadata={
                    "source": path.split("/")[-1],
                    "page": page_number + 1
                }
            )
            total_chunks += 1

    print(f"✅ {path} ingéré — {total_chunks} chunks ajoutés")

def main():
    print("🚀 Début ingestion")
    create_collection()
    for pdf in PDF_FILES:
        ingest_pdf(pdf)
    print("🎉 Ingestion terminée")

if __name__ == "__main__":
    main()