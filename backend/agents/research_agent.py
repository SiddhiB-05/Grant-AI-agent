import hashlib
import re
import time

from duckduckgo_search import DDGS

CACHE_VERSION = "v3"
_cache = {}

BLOCKLIST = (
    "upsc", "ctet", "neet", "jee", "exam", "recruitment", "sarkari",
    "job portal", "staff selection", "answer key", "result 20", "quiz",
    "wikipedia.org/wiki/list", "youtube.com", "facebook.com",
)

GRANT_SIGNALS = (
    "grant", "funding", "fellowship", "scheme", "csr", "foundation",
    "donor", "proposal", "ngo", "nonprofit", "subsidy", "financial assistance",
)

FALLBACK_GRANTS = [
    {
        "name": "FundsForNGOs — India Grants & Resources",
        "description": "Curated grant opportunities and funding alerts for Indian NGOs and nonprofits.",
        "url": "https://www.fundsforngos.org/india/",
        "deadline": "Ongoing listings",
        "amount": "Varies by program",
        "score": 0,
    },
    {
        "name": "NGO Grants Center",
        "description": "Database of international and India-focused grants for civil society organizations.",
        "url": "https://ngogrants.center/",
        "deadline": "Check listings",
        "amount": "Varies",
        "score": 0,
    },
    {
        "name": "CSR Hub — Corporate Social Responsibility India",
        "description": "CSR funding pathways and compliance resources for NGOs partnering with corporates.",
        "url": "https://www.csrhub.org/",
        "deadline": "Varies",
        "amount": "Varies",
        "score": 0,
    },
    {
        "name": "MyGov — Government Schemes & Innovation",
        "description": "Official portal for government schemes; search sector-specific programs for NGOs.",
        "url": "https://www.mygov.in/",
        "deadline": "Scheme-specific",
        "amount": "Scheme-specific",
        "score": 0,
    },
    {
        "name": "GrantStation — Funding Opportunities",
        "description": "Grant search tools and resources for nonprofits (verify India eligibility per listing).",
        "url": "https://grantstation.com/",
        "deadline": "Varies",
        "amount": "Varies",
        "score": 0,
    },
]


def _cache_key(query):
    raw = f"{CACHE_VERSION}:{query.lower().strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


def _parse_query(query):
    domain = ""
    location = ""
    for part in query.split("."):
        part = part.strip()
        if part.lower().startswith("domain:"):
            domain = part.split(":", 1)[1].strip()
        elif part.lower().startswith("location:"):
            location = part.split(":", 1)[1].strip()
    clean = query
    for label in ["Domain:", "Location:", "Budget:", "Goals:"]:
        clean = clean.replace(label, "")
    clean = " ".join(clean.split())[:200]
    return clean, domain, location


def _is_relevant(result):
    title = (result.get("title") or "").lower()
    body = (result.get("body") or result.get("snippet") or "").lower()
    url = (result.get("href") or result.get("url") or "").lower()
    blob = f"{title} {body} {url}"

    if any(block in blob for block in BLOCKLIST):
        return False
    if not any(signal in blob for signal in GRANT_SIGNALS):
        return False
    return True


def _build_queries(clean, domain, location):
    topic = domain or clean[:80]
    place = location or "India"
    return [
        f"NGO grant funding {topic} {place} application",
        f"government scheme grant {topic} India nonprofit",
        f"CSR funding opportunities {topic} {place}",
        f"foundation grants {topic} India eligibility",
        f"international NGO grant {topic} {place}",
    ]


def search_grants(query, domain=None, location=None):
    """Search grants via DuckDuckGo with filtering and curated fallback."""
    cache_key = _cache_key(f"{query}|{domain}|{location}")
    if cache_key in _cache:
        cached = _cache[cache_key]
        print(f"[research_agent] Cache hit - {len(cached)} grants")
        return {"grants": cached, "cache_hit": True}

    clean, parsed_domain, parsed_location = _parse_query(query)
    domain = domain or parsed_domain
    location = location or parsed_location

    grants = []
    seen_urls = set()

    for search_query in _build_queries(clean, domain, location):
        if len(grants) >= 8:
            break
        print(f"[research_agent] Searching: {search_query[:90]}")
        try:
            with DDGS() as ddgs:
                raw = ddgs.text(search_query, max_results=12)
                results = list(raw) if raw else []

            for result in results:
                if not _is_relevant(result):
                    continue
                url = result.get("href") or result.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                grants.append(
                    {
                        "name": result.get("title", "Funding opportunity"),
                        "description": (
                            result.get("body")
                            or result.get("snippet")
                            or result.get("title", "")
                        )[:400],
                        "url": url,
                        "deadline": "Verify on website",
                        "amount": "See program page",
                        "score": 0,
                    }
                )
                if len(grants) >= 8:
                    break
        except Exception as e:
            print(f"[research_agent] Search error: {e}")
            time.sleep(1)

    if len(grants) < 3:
        print("[research_agent] Adding curated funding directories (low search yield)")
        for item in FALLBACK_GRANTS:
            if item["url"] not in seen_urls:
                grants.append(dict(item))
                seen_urls.add(item["url"])
            if len(grants) >= 6:
                break

    print(f"[research_agent] Found {len(grants)} grants")
    if grants:
        _cache[cache_key] = grants

    return {"grants": grants, "cache_hit": False}
