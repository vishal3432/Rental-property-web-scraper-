import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import Base, check_db_connection, engine

settings = get_settings()
configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    if not check_db_connection():
        raise RuntimeError("Database is not reachable")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"}))
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def request_timeout_middleware(request: Request, call_next):
    try:
        return await asyncio.wait_for(call_next(request), timeout=settings.request_timeout)
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Request timed out") from exc


@app.get("/health/live")
@limiter.limit("30/minute")
def live(_: Request) -> dict:
    return {"status": "alive"}


@app.get("/health/ready")
@limiter.limit("30/minute")
def ready(_: Request) -> dict:
    try:
        check_db_connection()
        return {"status": "ready"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})


@app.get("/")
@limiter.limit("60/minute")
def health(_: Request) -> dict:
    return {"status": "ok"}


app.include_router(router)
