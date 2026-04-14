import numpy as np
from sqlalchemy.orm import Session

from app.models import Property


def recommend_similar(db: Session, property_id: int, limit: int = 5) -> list[Property]:
    source = db.query(Property).filter(Property.id == property_id).first()
    if not source or not source.embedding_vector:
        return []

    source_vec = np.array(source.embedding_vector)
    candidates = db.query(Property).filter(Property.id != property_id).all()
    scored: list[tuple[float, Property]] = []
    for item in candidates:
        if not item.embedding_vector:
            continue
        vec = np.array(item.embedding_vector)
        score = float(np.dot(source_vec, vec) / (np.linalg.norm(source_vec) * np.linalg.norm(vec)))
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]
