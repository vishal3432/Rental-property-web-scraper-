import logging

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.ml.deduplication import deduplicate_records
from app.ml.embeddings import embed_texts
from app.models import Property

logger = logging.getLogger(__name__)


def store_properties(db: Session, records: list[dict]) -> int:
    cleaned = deduplicate_records(records)
    texts = [f"{item['address']} {item['price_text']}" for item in cleaned]
    embeddings = embed_texts(texts)

    upsert_payload = []
    for item, embedding in zip(cleaned, embeddings, strict=False):
        upsert_payload.append(
            {
                "address": item["address"],
                "price_text": item["price_text"],
                "price_value": item["price_value"],
                "link": item["link"],
                "embedding_vector": embedding,
            }
        )

    if not upsert_payload:
        return 0

    stmt = insert(Property).values(upsert_payload)
    stmt = stmt.on_conflict_do_update(
        index_elements=["link"],
        set_={
            "address": stmt.excluded.address,
            "price_text": stmt.excluded.price_text,
            "price_value": stmt.excluded.price_value,
            "embedding_vector": stmt.excluded.embedding_vector,
        },
    )
    result = db.execute(stmt)
    count = result.rowcount or 0
    logger.info("Stored %s rows", count)
    return count
