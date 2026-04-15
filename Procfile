web: gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}
worker: celery -A app.tasks.celery_app.celery_app worker -Q scraping --loglevel=INFO
