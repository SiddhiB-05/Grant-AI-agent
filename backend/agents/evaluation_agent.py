from sklearn.metrics.pairwise import cosine_similarity

from utils.embeddings import get_embedding


def evaluate_grants(grants):

    user_query = "women healthcare NGO"

    query_embedding = get_embedding(user_query)

    for grant in grants:

        grant_embedding = get_embedding(
            grant["name"]
        )

        similarity = cosine_similarity(
            [query_embedding],
            [grant_embedding]
        )[0][0]

        grant["score"] = round(
            similarity * 100,
            2
        )

    return grants