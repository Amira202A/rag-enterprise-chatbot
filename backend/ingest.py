from pypdf import PdfReader
from app.services.document_service import add_document, create_collection

PDF_FILES = [
    "data/fichier1.pdf",
    "data/ml.pdf"
]


# 🔹 Chunking amélioré avec overlap
def chunk_text(text, chunk_size=700, overlap=120):

    chunks = []
    start = 0

    while start < len(text):

        end = start + chunk_size
        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def ingest_pdf(path):

    print(f"\n📄 Lecture du PDF : {path}")

    reader = PdfReader(path)

    for page_number, page in enumerate(reader.pages):

        # ignorer les 5 premières pages
        if page_number < 5:
            continue

        text = page.extract_text()

        if not text:
            continue

        chunks = chunk_text(text)

        for chunk in chunks:

            add_document(
                chunk,
                metadata={
                    "source": path.split("/")[-1],  # garder seulement le nom du fichier
                    "page": page_number + 1
                }
            )

    print(f"✅ {path} ingéré")


def main():

    print("🚀 Début ingestion")

    create_collection()

    for pdf in PDF_FILES:
        ingest_pdf(pdf)

    print("🎉 Ingestion terminée")


if __name__ == "__main__":
    main()