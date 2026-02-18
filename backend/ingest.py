from pypdf import PdfReader
from app.services.document_service import add_document, create_collection


PDF_PATH = "data/fichier1.pdf"


def extract_text_from_pdf(path):
    reader = PdfReader(path)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


def chunk_text(text, chunk_size=500):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i+chunk_size])
    return chunks


def main():
    print("Lecture du PDF...")
    text = extract_text_from_pdf(PDF_PATH)

    print("Découpage...")
    chunks = chunk_text(text)

    print("Envoi vers Qdrant...")
    for chunk in chunks:
        add_document(chunk)

    print("Ingestion terminée ✅")


if __name__ == "__main__":
    main()
