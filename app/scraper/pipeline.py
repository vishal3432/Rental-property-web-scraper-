import json
import logging

from sqlalchemy.orm import Session

from app.ml.deduplication import deduplicate_records
from app.ml.embeddings import embed_texts
from app.models import Property

logger = logging.getLogger(__name__)


def store_properties(db: Session, records: list[dict]) -> int:
    cleaned = deduplicate_records(records)
    texts = [f"{item['address']} {item['price_text']}" for item in cleaned]
    embeddings = embed_texts(texts)

    count = 0
    for item, embedding in zip(cleaned, embeddings, strict=False):
        # Check if property with this link already exists
        existing = db.query(Property).filter(Property.link == item["link"]).first()
        if existing:
            existing.address = item["address"]
            existing.price_text = item["price_text"]
            existing.price_value = item["price_value"]
            existing.embedding_json = json.dumps(embedding)
        else:
            db.add(Property(
                address=item["address"],
                price_text=item["price_text"],
                price_value=item["price_value"],
                link=item["link"],
                embedding_json=json.dumps(embedding),
            ))
        count += 1

    db.commit()
    logger.info("Stored %s rows", count)
    return count
