web: gunicorn -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT
worker: celery -A app.tasks.celery_app.celery_app worker -Q scraping --loglevel=INFO
