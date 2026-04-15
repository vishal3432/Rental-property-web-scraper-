from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "rental_worker",
    broker=settings.broker,
    backend=settings.backend,
)
celery_app.conf.task_routes = {"app.tasks.scrape_tasks.*": {"queue": "scraping"}}
