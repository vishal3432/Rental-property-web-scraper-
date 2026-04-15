from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def deduplicate_records(records: list[dict], threshold: float = 0.88) -> list[dict]:
    if not records:
        return []

    corpus = [f"{item['address']} {item['price_text']}" for item in records]
    matrix = TfidfVectorizer(stop_words="english").fit_transform(corpus)
    similarity = cosine_similarity(matrix)

    keep_indices: list[int] = []
    for idx in range(len(records)):
        if not keep_indices:
            keep_indices.append(idx)
            continue
        if max(similarity[idx][saved] for saved in keep_indices) < threshold:
            keep_indices.append(idx)

    return [records[i] for i in keep_indices]
