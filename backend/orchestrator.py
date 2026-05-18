from agents.research_agent import search_grants
from agents.evaluation_agent import evaluate_grants
from agents.drafting_agent import generate_proposal


def run_pipeline(user_query):
    print(f"[orchestrator] Starting pipeline for query: {user_query[:80]}")

    print("[orchestrator] Step 1: Searching for grants...")
    grants = search_grants(user_query)
    print(f"[orchestrator] Found {len(grants)} raw results.")

    print("[orchestrator] Step 2: Scoring and ranking grants...")
    ranked_grants = evaluate_grants(grants, user_query)
    print(f"[orchestrator] Top score: {ranked_grants[0]['score'] if ranked_grants else 'N/A'}")

    print("[orchestrator] Step 3: Generating proposal draft...")
    proposal = generate_proposal(user_query, top_grants=ranked_grants)

    return {
        "grants": ranked_grants,
        "proposal": proposal,
        "query": user_query
    }