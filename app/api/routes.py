import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ml.recommender import recommend_similar
from app.models import Property
from app.schemas.property import PropertyOut, RecommendationResponse, SearchResponse
from app.tasks.scrape_tasks import scrape_properties
from app.db.session import get_db

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


def verify_api_key(x_api_key: str = Header(None)) -> bool:
    """Verify API key from request header."""
    if not settings.api_key_enabled:
        return True
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    # In production, use proper secrets management
    # This is a simple example - use environment variables or secret managers
    expected_key = settings.api_key if hasattr(settings, 'api_key') else None
    
    if expected_key and x_api_key != expected_key:
        logger.warning(f"Invalid API key attempt")
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return True


@router.post("/scrape")
def trigger_scrape(
    api_key_valid: bool = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> dict:
    try:
        from app.scraper.http_client import ScraperClient
        from app.scraper.parser import parse_properties
        from app.scraper.pipeline import store_properties

        html = ScraperClient().get(settings.scrape_url)
        records = parse_properties(html)
        stored = store_properties(db, records)
        return {
            "status": "done",
            "scraped": len(records),
            "stored": stored,
        }
    except Exception as e:
        logger.error(f"Scrape failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/properties", response_model=list[PropertyOut])
def list_properties(
    limit: int = Query(default=100, ge=1, le=500, description="Number of properties to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
) -> list[PropertyOut]:
    """
    List rental properties with pagination.
    
    Query Parameters:
    - limit: Number of results (1-500, default 100)
    - offset: Pagination offset (default 0)
    """
    try:
        rows = (
            db.query(Property)
            .order_by(Property.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        logger.info(f"Retrieved {len(rows)} properties (limit={limit}, offset={offset})")
        return rows
    except Exception as e:
        logger.error(f"Error listing properties: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve properties")


@router.get("/search", response_model=SearchResponse)
def search_properties(
    q: str = Query(..., min_length=2, max_length=100, description="Search query (address)"),
    min_price: float | None = Query(default=None, ge=0, description="Minimum price"),
    max_price: float | None = Query(default=None, ge=0, description="Maximum price"),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> SearchResponse:
    """
    Search for properties by address and price range.
    
    Query Parameters:
    - q: Search query (required, 2-100 chars)
    - min_price: Minimum price filter (optional)
    - max_price: Maximum price filter (optional)
    - limit: Number of results (default 100)
    """
    try:
        logger.info(f"Searching properties: q={q}, min={min_price}, max={max_price}")
        
        query = db.query(Property).filter(Property.address.ilike(f"%{q}%"))
        
        if min_price is not None:
            if min_price < 0:
                raise ValueError("min_price must be >= 0")
            query = query.filter(Property.price_value >= min_price)
        
        if max_price is not None:
            if max_price < 0:
                raise ValueError("max_price must be >= 0")
            if min_price is not None and max_price < min_price:
                raise ValueError("max_price must be >= min_price")
            query = query.filter(Property.price_value <= max_price)
        
        items = query.limit(limit).all()
        logger.info(f"Found {len(items)} properties matching search")
        
        return SearchResponse(count=len(items), items=items)
    except ValueError as e:
        logger.warning(f"Invalid search parameters: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching properties: {e}")
        raise HTTPException(status_code=500, detail="Failed to search properties")


@router.get("/recommend", response_model=RecommendationResponse)
def recommend(
    property_id: int = Query(..., ge=1, description="Property ID to get recommendations for"),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    """
    Get similar property recommendations.
    
    Query Parameters:
    - property_id: Property ID (required)
    - limit: Number of recommendations (default 10, max 50)
    """
    try:
        logger.info(f"Getting recommendations for property {property_id}")
        
        source = db.query(Property).filter(Property.id == property_id).first()
        if not source:
            logger.warning(f"Property {property_id} not found")
            raise HTTPException(status_code=404, detail="Property not found")
        
        recs = recommend_similar(db, property_id, limit=limit)
        logger.info(f"Found {len(recs)} recommendations for property {property_id}")
        
        return RecommendationResponse(source_property_id=property_id, recommendations=recs)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")


@router.get("/task/{task_id}")
def get_task_status(task_id: str) -> dict:
    """
    Get the status of a scraping task.
    
    Path Parameters:
    - task_id: Celery task ID
    """
    try:
        from app.tasks.celery_app import celery_app
        
        task = celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": task.status,
            "result": task.result if task.successful() else None,
            "error": str(task.info) if task.failed() else None,
        }
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task status")

