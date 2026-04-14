from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import verify_api_key
from app.db.session import get_db
from app.ml.recommender import recommend_similar
from app.models import Property
from app.schemas.property import PropertyOut, RecommendationResponse, SearchResponse
from app.tasks.scrape_tasks import scrape_properties

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/scrape")
def trigger_scrape() -> dict:
    task = scrape_properties.delay()
    return {"task_id": task.id, "status": "queued"}


@router.get("/properties", response_model=list[PropertyOut])
def list_properties(
    limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)
) -> list[PropertyOut]:
    rows = db.query(Property).order_by(Property.created_at.desc()).limit(limit).all()
    return rows


@router.get("/search", response_model=SearchResponse)
def search_properties(
    q: str = Query(..., min_length=2, max_length=200),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
) -> SearchResponse:
    query = db.query(Property).filter(Property.address.ilike(f"%{q}%"))
    if min_price is not None:
        query = query.filter(Property.price_value >= min_price)
    if max_price is not None:
        query = query.filter(Property.price_value <= max_price)
    items = query.limit(100).all()
    return SearchResponse(count=len(items), items=items)


@router.get("/recommend", response_model=RecommendationResponse)
def recommend(
    property_id: int = Query(..., ge=1), db: Session = Depends(get_db)
) -> RecommendationResponse:
    source = db.query(Property).filter(Property.id == property_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Property not found")
    recs = recommend_similar(db, property_id)
    return RecommendationResponse(source_property_id=property_id, recommendations=recs)
