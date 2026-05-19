import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

FALLBACK_MODELS = ["gemini-2.0-flash", "gemini-2.0-flash-001", "gemini-2.5-flash"]
DRAFTING_PREFER = ["gemini-2.0-flash", "gemini-2.0-flash-001", "gemini-2.5-flash"]
DRAFTING_SKIP = ("lite", "image", "preview", "thinking", "exp")

MAX_WORDS = 650
TARGET_WORDS = "300-400"
MAX_PROPOSAL_CHARS = 3200

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
LIST_URL = "https://generativelanguage.googleapis.com/v1beta/models?key={key}"


def _result(text, model=None, truncated=False):
    return {"text": text, "model": model, "truncated": truncated}


def _enforce_word_limit(text: str) -> tuple[str, bool]:
    if not text:
        return text, False
    text = re.sub(r"[ \t]{6,}", " ", text)
    text = re.sub(r"\n{4,}", "\n\n", text)
    words = text.split()
    if len(words) <= MAX_WORDS:
        return text.strip(), False
    trimmed = " ".join(words[:MAX_WORDS]).strip()
    if not trimmed.endswith("."):
        trimmed += "..."
    return trimmed, True


def _clean_proposal(text: str) -> tuple[str, bool]:
    """Clean and validate proposal text, removing artifacts and enforcing limits."""
    if not text:
        return text, False
    
    # Remove API artifacts
    text = re.sub(r"\*Generation hit the token limit.*", "", text, flags=re.I)
    text = re.sub(r"\*Output trimmed.*", "", text, flags=re.I)
    text = re.sub(r"---\s*\n\*[^*]+\*", "", text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Character limit (safety)
    if len(text) > MAX_PROPOSAL_CHARS:
        text = text[:MAX_PROPOSAL_CHARS].rsplit(" ", 1)[0] + "..."
    
    # Word limit enforcement
    text, truncated = _enforce_word_limit(text)
    
    # Ensure we have actual content
    if not text or len(text.strip()) < 50:
        return "", True
    
    return text, truncated


def _models_for_drafting(available):
    pool = [m for m in available if not any(s in m.lower() for s in DRAFTING_SKIP)]
    ordered = [m for m in DRAFTING_PREFER if m in pool]
    for model in pool:
        if model not in ordered:
            ordered.append(model)
    return ordered or list(FALLBACK_MODELS)


def _get_available_models():
    try:
        response = requests.get(LIST_URL.format(key=API_KEY), timeout=10)
        data = response.json()
        models = []
        for model in data.get("models", []):
            name = model.get("name", "")
            if "generateContent" in model.get("supportedGenerationMethods", []):
                models.append(name.replace("models/", ""))
        return _models_for_drafting(models)
    except Exception as e:
        print(f"[drafting_agent] Model list failed: {e}")
        return FALLBACK_MODELS


def _extract_text(candidate):
    parts = candidate.get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts if p.get("text") and not p.get("thought"))


def _call(model, prompt):
    """Call Gemini API with proper error handling."""
    url = BASE_URL.format(model=model, key=API_KEY)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.35,
            "maxOutputTokens": 2048,  # Increased to allow full proposal generation
        },
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=90
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"[drafting_agent] HTTP Error calling {model}: {e.response.status_code} - {e.response.text[:200]}")
        return {"error": {"message": f"HTTP {e.response.status_code}: {e.response.reason}"}}
    except Exception as e:
        print(f"[drafting_agent] Error calling {model}: {str(e)}")
        raise


def generate_proposal(user_query, top_grants=None, org_name=None):
    """Generate a professional grant proposal using Gemini API."""
    if not API_KEY:
        error_msg = "Error: GEMINI_API_KEY is not set in your .env file."
        print(f"[drafting_agent] {error_msg}")
        return _result(error_msg)

    grants_context = ""
    if top_grants:
        grants_context = "\nRelevant funding sources (reference briefly if useful):\n"
        for i, grant in enumerate(top_grants[:2], 1):
            grants_context += f"- {grant.get('name', 'N/A')}\n"

    org_line = f"Organization: {org_name}\n" if org_name else ""

    prompt = f"""Write a professional grant concept note for an Indian NGO.

{org_line}Project:
{user_query}
{grants_context}

STRICT RULES:
- Total length: {TARGET_WORDS} words ONLY (never exceed {MAX_WORDS} words).
- Plain professional English. No filler, no repetition, no markdown tables.
- Use exactly these section headings on their own line:

PROJECT TITLE
EXECUTIVE SUMMARY
PROBLEM & NEED
APPROACH & ACTIVITIES
EXPECTED IMPACT
BUDGET SUMMARY
CONCLUSION

Keep each section short (2-4 sentences or 3-5 bullets for Approach).
Stop immediately after CONCLUSION."""

    models_to_try = _get_available_models()
    last_error = ""

    for model in models_to_try[:4]:
        try:
            print(f"[drafting_agent] Trying model: {model}")
            result = _call(model, prompt)

            # Check for API errors
            if "error" in result:
                error_msg = result["error"].get("message", "Unknown error")
                last_error = error_msg
                print(f"[drafting_agent] API Error on {model}: {error_msg[:100]}")
                continue

            candidates = result.get("candidates") or []
            if not candidates:
                last_error = f"No candidates returned from {model}"
                print(f"[drafting_agent] {last_error}")
                continue

            candidate = candidates[0]
            
            # Check for safety filtering
            if candidate.get("finishReason") == "SAFETY":
                error_msg = "Blocked by safety filters. Try simpler project wording."
                print(f"[drafting_agent] Safety filter triggered")
                return _result(error_msg)

            # Extract text from response
            text = _extract_text(candidate)
            if not text or not text.strip():
                last_error = f"Empty text returned from {model}"
                print(f"[drafting_agent] {last_error}")
                continue

            print(f"[drafting_agent] Raw text length: {len(text)} chars")
            
            # Clean and validate proposal
            text, trimmed = _clean_proposal(text)
            
            if not text or len(text.strip()) < 100:
                last_error = f"Proposal too short after cleaning ({len(text)} chars)"
                print(f"[drafting_agent] {last_error}")
                continue
            
            finish = candidate.get("finishReason", "")
            truncated = trimmed or finish == "MAX_TOKENS"
            word_count = len(text.split())
            print(f"[drafting_agent] SUCCESS {model}: {word_count} words, finish={finish}, truncated={truncated}")
            return _result(text, model=model, truncated=truncated)

        except requests.exceptions.Timeout:
            last_error = f"Timeout on {model} (>90s)"
            print(f"[drafting_agent] {last_error}")
            continue
        except requests.exceptions.ConnectionError as e:
            last_error = f"Connection error: {str(e)[:50]}"
            print(f"[drafting_agent] {last_error}")
            continue
        except Exception as e:
            last_error = f"Unexpected error: {str(e)[:100]}"
            print(f"[drafting_agent] {last_error}")
            continue

    # All models failed - return helpful error
    error_msg = (
        "Could not generate proposal after trying all available models.\n\n"
        f"Last error: {last_error}\n\n"
        "Troubleshooting:\n"
        "1. Verify GEMINI_API_KEY is set in .env\n"
        "2. Check API quota at https://aistudio.google.com\n"
        "3. Try with simpler project description"
    )
    print(f"[drafting_agent] Final fallback: {error_msg[:100]}")
    return _result(error_msg)
