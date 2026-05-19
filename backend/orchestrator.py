import time

from agents.drafting_agent import generate_proposal
from agents.evaluation_agent import evaluate_grants
from agents.research_agent import search_grants


def run_pipeline(user_query, org_name=None, location=None, budget=None, domain=None):

    print(f"[orchestrator] Starting pipeline")

    metrics = {
        "steps": {},
        "cache_hit": False,
    }

    # -----------------------------
    # SEARCH
    # -----------------------------
    t0 = time.perf_counter()

    search_result = search_grants(
        user_query,
        domain=domain,
        location=location,
    )

    grants = search_result.get("grants", [])

    metrics["cache_hit"] = search_result.get("cache_hit", False)
    metrics["grants_found"] = len(grants)

    metrics["steps"]["search_ms"] = round(
        (time.perf_counter() - t0) * 1000
    )

    # -----------------------------
    # RANK
    # -----------------------------
    t1 = time.perf_counter()

    ranked_grants = []

    if grants:
        ranked_grants = evaluate_grants(grants, user_query)

    metrics["steps"]["rank_ms"] = round(
        (time.perf_counter() - t1) * 1000
    )

    metrics["top_fit_score"] = (
        ranked_grants[0]["score"]
        if ranked_grants else 0
    )

    # -----------------------------
    # BUILD CONTEXT
    # -----------------------------
    proposal_context = user_query

    extra_context = []

    if org_name:
        extra_context.append(f"Organization: {org_name}")

    if location:
        extra_context.append(f"Location: {location}")

    if budget:
        extra_context.append(f"Budget: {budget}")

    if domain:
        extra_context.append(f"Domain: {domain}")

    if extra_context:
        proposal_context += "\n" + "\n".join(extra_context)

    # -----------------------------
    # DRAFT
    # -----------------------------
    t2 = time.perf_counter()

    try:

        draft = generate_proposal(
            proposal_context,
            top_grants=ranked_grants[:3],
            org_name=org_name,
        )

        proposal = draft.get("text", "")

    except Exception as e:

        print(f"[orchestrator] Drafting failed: {e}")

        proposal = (
            "Proposal generation failed. "
            "Please check Gemini API configuration."
        )

        draft = {
            "model": None,
            "truncated": False,
        }

    metrics["steps"]["draft_ms"] = round(
        (time.perf_counter() - t2) * 1000
    )

    metrics["total_ms"] = round(
        (time.perf_counter() - t0) * 1000
    )

    metrics["model"] = draft.get("model")

    metrics["proposal_words"] = (
        len(proposal.split()) if proposal else 0
    )

    return {
        "grants": ranked_grants,
        "proposal": proposal,
        "query": user_query,
        "org_name": org_name or "",
        "domain": domain or "",
        "location": location or "",
        "budget": budget or "",
        "metrics": metrics,
        "proposal_truncated": draft.get("truncated", False),
    }