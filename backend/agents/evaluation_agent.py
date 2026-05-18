from sklearn.metrics.pairwise import cosine_similarity
from utils.embeddings import get_embedding


def evaluate_grants(grants, user_query):
    """
    Score each grant by semantic similarity to user query.
    Uses name + description for embedding.
    Normalizes scores so best = 100%, worst = 0%.
    Returns grants sorted highest first.
    """

    if not grants:
        return []

    try:
        query_embedding = get_embedding(user_query)
    except Exception as e:
        print(f"[evaluation_agent] Failed to embed query: {e}")
        return grants

    raw_scores = []

    for grant in grants:
        try:
            text = f"{grant.get('name', '')}. {grant.get('description', '')}".strip()
            if not text:
                grant["_raw"] = 0.0
                raw_scores.append(0.0)
                continue

            emb = get_embedding(text)
            sim = float(cosine_similarity([query_embedding], [emb])[0][0])
            grant["_raw"] = sim
            raw_scores.append(sim)

        except Exception as e:
            print(f"[evaluation_agent] Error scoring '{grant.get('name')}': {e}")
            grant["_raw"] = 0.0
            raw_scores.append(0.0)

    # Normalize so best match = 100%, worst = 0%
    lo, hi = min(raw_scores), max(raw_scores)
    span = hi - lo

    for grant in grants:
        raw = grant.pop("_raw", 0.0)
        normalized = ((raw - lo) / span) if span > 0 else 1.0
        grant["score"] = round(normalized * 100, 1)

    grants.sort(key=lambda g: g["score"], reverse=True)
    return grants