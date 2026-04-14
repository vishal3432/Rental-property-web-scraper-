import logging

from requests import RequestException

from app.core.config import get_settings
from app.db.session import db_session_scope
from app.scraper.http_client import ScraperClient
from app.scraper.parser import ParseError, parse_properties
from app.scraper.pipeline import store_properties
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task(
    name="app.tasks.scrape_tasks.scrape_properties",
    bind=True,
    autoretry_for=(RequestException, ParseError),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def scrape_properties(self) -> dict:
    try:
        html = ScraperClient().get(settings.scrape_url)
        records = parse_properties(html)
        with db_session_scope() as db:
            stored = store_properties(db, records)
        return {"scraped": len(records), "stored": stored}
    except Exception as exc:
        logger.exception("Scraping task failed")
        raise exc
