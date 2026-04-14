import logging

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.scraper.http_client import ScraperClient
from app.scraper.parser import parse_properties
from app.scraper.pipeline import store_properties
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task(name="app.tasks.scrape_tasks.scrape_properties")
def scrape_properties() -> dict:
    db = SessionLocal()
    try:
        html = ScraperClient().get(settings.scrape_url)
        records = parse_properties(html)
        stored = store_properties(db, records)
        return {"scraped": len(records), "stored": stored}
    except Exception as exc:
        logger.exception("Scraping task failed")
        raise exc
    finally:
        db.close()
