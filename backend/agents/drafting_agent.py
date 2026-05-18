import requests
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# Step 1: Try to auto-discover working models from YOUR API key
# Step 2: Fall back to this hardcoded list (confirmed working May 2026)
FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
LIST_URL = "https://generativelanguage.googleapis.com/v1beta/models?key={key}"


def _get_available_models():
    """
    Fetch the list of models available for THIS API key from Google.
    Returns a list of model IDs that support generateContent, best ones first.
    """
    try:
        r = requests.get(LIST_URL.format(key=API_KEY), timeout=10)
        data = r.json()
        models = []
        for m in data.get("models", []):
            name = m.get("name", "")          # e.g. "models/gemini-2.0-flash"
            actions = m.get("supportedGenerationMethods", [])
            if "generateContent" in actions:
                model_id = name.replace("models/", "")
                models.append(model_id)

        # Prefer flash models — sort: 2.5 first, then 2.0, then others
        def rank(m):
            if "2.5-flash" in m and "preview" not in m: return 0
            if "2.0-flash" in m and "lite" not in m and "preview" not in m: return 1
            if "2.0-flash-lite" in m: return 2
            if "flash" in m and "preview" not in m: return 3
            if "preview" in m: return 9
            return 5

        models.sort(key=rank)
        print(f"[drafting_agent] Available models: {models[:5]}")
        return models if models else FALLBACK_MODELS

    except Exception as e:
        print(f"[drafting_agent] Could not list models: {e} — using fallback list")
        return FALLBACK_MODELS


def _call(model, prompt):
    url = BASE_URL.format(model=model, key=API_KEY)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}
    }
    r = requests.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    return r.json()


def generate_proposal(user_query, top_grants=None):
    if not API_KEY:
        return "Error: GEMINI_API_KEY is not set in your .env file."

    # Build grants context
    grants_context = ""
    if top_grants:
        top3 = top_grants[:3]
        grants_context = "\n\nTop matched grant opportunities:\n"
        for i, g in enumerate(top3, 1):
            grants_context += (
                f"{i}. {g.get('name', 'N/A')} "
                f"(Fit: {g.get('score', 0)}%) — {g.get('description', '')[:200]}\n"
            )

    prompt = f"""You are an expert grant writer. Write a detailed professional grant proposal.

Project Description:
{user_query}
{grants_context}

Include these sections:
1. Executive Summary
2. Problem Statement
3. Project Goals and Objectives
4. Methodology / Implementation Plan
5. Expected Outcomes and Impact
6. Budget Overview
7. Organization Background
8. Conclusion

Use formal, compelling language with measurable outcomes."""

    # Get models available for this API key, then try each one
    models_to_try = _get_available_models()
    last_error = ""

    for model in models_to_try[:5]:   # try up to 5 models max
        try:
            print(f"[drafting_agent] Trying: {model}")
            result = _call(model, prompt)

            if "error" in result:
                last_error = result["error"].get("message", "Unknown error")
                print(f"[drafting_agent] {model} failed: {last_error[:80]}")
                continue

            if "candidates" in result and result["candidates"]:
                candidate = result["candidates"][0]
                if candidate.get("finishReason") == "SAFETY":
                    return "Blocked by Gemini safety filters. Try rephrasing your project description."
                text = candidate["content"]["parts"][0]["text"]
                print(f"[drafting_agent] Success with: {model}")
                return text

            last_error = f"Unexpected response from {model}"

        except requests.exceptions.Timeout:
            last_error = f"Timeout on {model}"
            print(f"[drafting_agent] {last_error}")
            continue
        except Exception as e:
            last_error = str(e)
            print(f"[drafting_agent] Exception on {model}: {last_error}")
            continue

    return (
        f"Could not generate proposal. All models failed.\n"
        f"Last error: {last_error}\n\n"
        f"Please check:\n"
        f"1. Your GEMINI_API_KEY in .env is valid\n"
        f"2. Quota not exceeded — visit https://aistudio.google.com\n"
        f"3. Generative Language API is enabled in Google Cloud Console"
    )