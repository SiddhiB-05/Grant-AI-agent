from agents.research_agent import search_grants
from agents.evaluation_agent import evaluate_grants
from agents.drafting_agent import generate_proposal


def run_pipeline():

    grants = search_grants("NGO")

    ranked_grants = evaluate_grants(grants)

    proposal = generate_proposal()

    return {
        "grants": ranked_grants,
        "proposal": proposal
    }