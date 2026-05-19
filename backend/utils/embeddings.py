from sentence_transformers import SentenceTransformer

_model = None


def _get_model():
    global _model
    if _model is None:
        print("[embeddings] Loading SentenceTransformer model... (first request may take ~30s)")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[embeddings] Model ready.")
    return _model


def get_embedding(text: str):
    """Return embedding vector for the given text."""
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text.")
    return _get_model().encode(text[:512])
