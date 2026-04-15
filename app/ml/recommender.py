import json

import numpy as np
from sqlalchemy.orm import Session

from app.models import Property


def _as_vector(raw: str | None) -> np.ndarray | None:
    if not raw:
        return None
    return np.array(json.loads(raw))


def recommend_similar(db: Session, property_id: int, limit: int = 5) -> list[Property]:
    source = db.query(Property).filter(Property.id == property_id).first()
    if not source:
        return []

    source_vec = _as_vector(source.embedding_json)
    if source_vec is None:
        return []

    candidates = db.query(Property).filter(Property.id != property_id).all()
    scored: list[tuple[float, Property]] = []
    for item in candidates:
        vec = _as_vector(item.embedding_json)
        if vec is None:
            continue
        score = float(np.dot(source_vec, vec) / (np.linalg.norm(source_vec) * np.linalg.norm(vec)))
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]
