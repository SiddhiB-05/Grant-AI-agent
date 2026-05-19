from sklearn.metrics.pairwise import cosine_similarity

from utils.embeddings import get_embedding


# =========================================================
# QUALITY SIGNALS
# =========================================================

HIGH_QUALITY_DOMAINS = (
    ".gov",
    "grants.gov",
    "fundsforngos",
    "unicef",
    "undp",
    "worldbank",
    "usaid",
    "foundation",
    "fordfoundation",
    "gatesfoundation",
)

GRANT_KEYWORDS = (
    "grant",
    "funding",
    "apply",
    "proposal",
    "eligibility",
    "nonprofit",
    "ngo",
    "foundation",
    "award",
    "financial support",
)

BAD_SIGNALS = (
    "what is csr",
    "investopedia",
    "tax",
    "law",
    "compliance",
    "definition",
    "guide",
    "explained",
)


# =========================================================
# HELPERS
# =========================================================

def _quality_bonus(grant):

    score = 0

    url = (grant.get("url") or "").lower()

    text = (
        f"{grant.get('name', '')} "
        f"{grant.get('description', '')}"
    ).lower()

    # -------------------------
    # GOOD DOMAIN BOOST
    # -------------------------

    for domain in HIGH_QUALITY_DOMAINS:
        if domain in url:
            score += 0.08
            break

    # -------------------------
    # GRANT KEYWORDS
    # -------------------------

    keyword_hits = sum(
        1 for kw in GRANT_KEYWORDS
        if kw in text
    )

    score += min(keyword_hits * 0.015, 0.08)

    # -------------------------
    # BAD CONTENT PENALTY
    # -------------------------

    for bad in BAD_SIGNALS:
        if bad in text:
            score -= 0.15

    return score


def _calibrated_score(raw_similarity):

    """
    Convert cosine similarity into realistic
    human-readable relevance score.
    """

    # Typical semantic similarity ranges:
    # 0.20 weak
    # 0.35 decent
    # 0.50 strong
    # 0.65 excellent

    scaled = raw_similarity * 100

    # Compression curve
    if scaled < 25:
        final = 20 + (scaled * 0.6)

    elif scaled < 45:
        final = 35 + ((scaled - 25) * 1.2)

    else:
        final = 60 + ((scaled - 45) * 0.9)

    return max(12, min(96, final))


def _label(score):

    if score >= 78:
        return "Strong Match"

    if score >= 55:
        return "Relevant Match"

    if score >= 35:
        return "Possible Match"

    return "Weak Match"


# =========================================================
# MAIN EVALUATION
# =========================================================

def evaluate_grants(grants, user_query):

    """
    Evaluate grants using:
    - semantic similarity
    - domain quality
    - grant keyword signals
    - content penalties

    Returns cleaner realistic rankings.
    """

    if not grants:
        return []

    try:

        query_embedding = get_embedding(user_query)

    except Exception as e:

        print(f"[evaluation_agent] Query embedding failed: {e}")

        return grants

    ranked = []

    for grant in grants:

        try:

            text = (
                f"{grant.get('name', '')}. "
                f"{grant.get('description', '')}"
            ).strip()

            if not text:
                continue

            emb = get_embedding(text)

            similarity = float(
                cosine_similarity(
                    [query_embedding],
                    [emb]
                )[0][0]
            )

            # -------------------------
            # QUALITY BOOSTS
            # -------------------------

            similarity += _quality_bonus(grant)

            # clamp
            similarity = max(0.0, min(0.95, similarity))

            # -------------------------
            # HUMAN SCORE
            # -------------------------

            score = round(
                _calibrated_score(similarity),
                1
            )

            grant["score"] = score

            grant["match_label"] = _label(score)

            grant["raw_similarity"] = round(similarity, 3)

            ranked.append(grant)

        except Exception as e:

            print(
                f"[evaluation_agent] Failed scoring "
                f"{grant.get('name')}: {e}"
            )

    # -------------------------------------------------
    # SORT
    # -------------------------------------------------

    ranked.sort(
        key=lambda g: g.get("score", 0),
        reverse=True,
    )

    return ranked