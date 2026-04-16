import logging
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

# Module-level vectorizer — fits on first call
_vectorizer: TfidfVectorizer | None = None
_vocab_corpus: list[str] = []


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate TF-IDF embeddings for a list of texts.
    Falls back gracefully if texts are empty.
    """
    global _vectorizer, _vocab_corpus

    if not texts:
        return []

    try:
        vectorizer = TfidfVectorizer(max_features=128)
        matrix = vectorizer.fit_transform(texts)
        return [row.toarray().flatten().tolist() for row in matrix]
    except Exception as e:
        logger.warning(f"Embedding failed, using zero vectors: {e}")
        return [[0.0] * 128 for _ in texts]
