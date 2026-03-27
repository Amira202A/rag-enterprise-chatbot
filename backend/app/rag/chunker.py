def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50):
    """
    Découpe le texte en morceaux avec overlap
    pour améliorer la recherche vectorielle.
    """

    chunks = []
    start = 0

    while start < len(text):

        end = start + chunk_size
        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks