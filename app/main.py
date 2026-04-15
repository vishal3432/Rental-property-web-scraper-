import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import Base, engine, get_db

logger = logging.getLogger(__name__)
settings = get_settings()

configure_logging()


async def check_database_health() -> dict:
    """Check database connectivity and health."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "database": f"error: {str(e)[:100]}"}


async def check_redis_health() -> dict:
    """Check Redis connectivity and health."""
    try:
        from app.tasks.celery_app import celery_app
        celery_app.connection_or_acquire().release()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"status": "unhealthy", "redis": f"error: {str(e)[:100]}"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    logger.info("🚀 Starting application...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created/verified")
    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down application...")
    engine.dispose()
    logger.info("✓ Database connections closed")


app = FastAPI(
    title="Rental Scraper API",
    description="Web scraper API for rental properties with ML-powered recommendations",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=settings.allow_credentials,
    allow_methods=settings.allow_methods,
    allow_headers=settings.allow_headers,
)

# Include API routes
app.include_router(router, prefix=settings.api_prefix)


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Welcome to Rental Property Scraper API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health/live")
async def health_live() -> dict:
    """Liveness probe - is the application running?"""
    return {
        "status": "alive",
        "service": "rental-scraper-api",
    }


@app.get("/health/ready")
async def health_ready(db: Session = Depends(get_db)) -> dict:
    """Readiness probe - is the application ready to serve requests?"""
    health_status = {
        "status": "ready",
        "checks": {},
    }
    
    # Check database
    db_health = await check_database_health()
    health_status["checks"]["database"] = db_health
    
    # Check Redis
    redis_health = await check_redis_health()
    health_status["checks"]["redis"] = redis_health
    
    # Overall status
    if (
        db_health.get("status") == "healthy"
        and redis_health.get("status") == "healthy"
    ):
        health_status["status"] = "ready"
        health_status["overall"] = "healthy"
    else:
        health_status["status"] = "not_ready"
        health_status["overall"] = "unhealthy"
    
    return health_status


@app.get("/health/deep")
async def health_deep(db: Session = Depends(get_db)) -> dict:
    """Deep health check - detailed system information."""
    import os
    import platform
    
    return {
        "status": "healthy",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": {
            "debug": settings.debug,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "services": {
            "database": await check_database_health(),
            "redis": await check_redis_health(),
        },
    }

