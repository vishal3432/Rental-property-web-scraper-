from fastapi import FastAPI

from app.api.routes import router
from app.core.logging import configure_logging
from app.db.session import Base, engine

configure_logging()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rental Scraper API")
app.include_router(router)


@app.get("/")
def health() -> dict:
    return {"status": "ok"}
