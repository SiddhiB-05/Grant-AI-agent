from sentence_transformers import SentenceTransformer

# Load model SYNCHRONOUSLY at import time.
# This blocks Flask startup for ~30s but guarantees the model
# is ALWAYS ready before any request is served.
print("[embeddings] Loading SentenceTransformer model... (this takes ~30s on first run)")
_model = SentenceTransformer("all-MiniLM-L6-v2")
print("[embeddings] Model ready.")


def get_embedding(text: str):
    """Return embedding vector for the given text."""
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text.")
    return _model.encode(text[:512])