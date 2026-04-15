import logging
from celery import Task
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.scraper.http_client import ScraperClient
from app.scraper.parser import parse_properties
from app.scraper.pipeline import store_properties
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


class CallbackTask(Task):
    """Task class with error handling and logging."""
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(
            f"Task {self.name} (id={task_id}) retrying due to: {exc}"
        )
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails permanently."""
        logger.error(
            f"Task {self.name} (id={task_id}) failed permanently. "
            f"Error: {exc}",
            exc_info=einfo,
        )
    
    def on_success(self, result, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(f"Task {self.name} (id={task_id}) completed successfully: {result}")


@celery_app.task(
    name="app.tasks.scrape_tasks.scrape_properties",
    base=CallbackTask,
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={
        "max_retries": settings.max_retries,
        "countdown": settings.retry_delay_seconds,
    },
    default_retry_delay=settings.retry_delay_seconds,
    acks_late=True,
    reject_in_progress=True,
)
def scrape_properties(self) -> dict:
    """
    Scrape rental properties from the target website.
    
    Automatically retries up to MAX_RETRIES times with exponential backoff.
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting scrape task (attempt {self.request.retries + 1}/{settings.max_retries + 1})")
        
        # Fetch HTML content
        html = ScraperClient().get(settings.scrape_url)
        if not html:
            raise ValueError("Failed to retrieve HTML content")
        
        logger.info(f"Retrieved HTML content ({len(html)} bytes)")
        
        # Parse properties
        records = parse_properties(html)
        logger.info(f"Parsed {len(records)} properties from HTML")
        
        # Store in database
        stored = store_properties(db, records)
        logger.info(f"Stored {stored} properties in database")
        
        result = {
            "status": "success",
            "scraped": len(records),
            "stored": stored,
            "attempt": self.request.retries + 1,
        }
        
        logger.info(f"✓ Scrape task completed: {result}")
        return result
        
    except Exception as exc:
        logger.error(
            f"Scrape task failed (attempt {self.request.retries + 1}): {exc}",
            exc_info=True,
        )
        
        # Retry with exponential backoff
        retry_delay = int(
            settings.retry_delay_seconds * (settings.retry_backoff_seconds ** self.request.retries)
        )
        logger.info(f"Retrying in {retry_delay} seconds...")
        
        raise self.retry(exc=exc, countdown=retry_delay)
        
    finally:
        db.close()

