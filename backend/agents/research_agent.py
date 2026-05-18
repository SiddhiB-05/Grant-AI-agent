import time
import hashlib
from duckduckgo_search import DDGS

# Simple in-memory cache — stores results per query so same search
# always returns same cards and doesn't call DuckDuckGo twice
_cache = {}


def _cache_key(query):
    return hashlib.md5(query.lower().strip().encode()).hexdigest()


def search_grants(query):
    """
    Search for grant opportunities using DuckDuckGo.
    - Caches results so repeated searches return the same cards
    - Tries multiple query variants as fallback
    """

    cache_key = _cache_key(query)
    if cache_key in _cache:
        print(f"[research_agent] Cache hit — returning {len(_cache[cache_key])} cached grants")
        return _cache[cache_key]

    # Strip form labels like "Domain:", "Location:" — bad for search
    clean = query
    for label in ["Domain:", "Location:", "Budget:", "Goals:"]:
        clean = clean.replace(label, "")
    clean = " ".join(clean.split())[:200]

    queries = [
        f"grant funding opportunities {clean}",
        f"government grant scheme {clean} apply",
        f"NGO funding {clean} eligibility",
        f"grant {clean}",
    ]

    grants = []
    seen_urls = set()

    for search_query in queries:
        if len(grants) >= 8:
            break

        print(f"[research_agent] Searching: {search_query[:80]}")
        try:
            with DDGS() as ddgs:
                raw = ddgs.text(search_query, max_results=10)
                results = list(raw) if raw else []

            for r in results:
                url = r.get("href") or r.get("url", "")
                if url and url in seen_urls:
                    continue
                if url:
                    seen_urls.add(url)
                grants.append({
                    "name": r.get("title", "Unnamed Grant"),
                    "description": r.get("body") or r.get("snippet") or r.get("title", ""),
                    "url": url,
                    "deadline": "Check website",
                    "amount": "Varies",
                    "score": 0
                })

            if len(grants) >= 5:
                break

        except Exception as e:
            print(f"[research_agent] Search error: {e}")
            time.sleep(1)

    print(f"[research_agent] Found {len(grants)} grants")

    # Cache so next request for same query is instant
    if grants:
        _cache[cache_key] = grants

    return grants