from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "rental_worker",
    broker=settings.broker,
    backend=settings.backend,
)
celery_app.conf.update(
    task_routes={"app.tasks.scrape_tasks.*": {"queue": "scraping"}},
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
