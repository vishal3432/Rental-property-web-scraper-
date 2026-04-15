from collections.abc import Generator
import logging

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure connection pool based on environment
if settings.debug or "sqlite" in settings.database_url:
    # Development: use NullPool for SQLite or debug mode
    poolclass = NullPool
    pool_kwargs = {}
else:
    # Production: use QueuePool with sizing
    poolclass = QueuePool
    pool_kwargs = {
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_recycle": settings.db_pool_recycle,
        "pool_pre_ping": True,  # Verify connection before using
    }

engine = create_engine(
    settings.database_url,
    poolclass=poolclass,
    **pool_kwargs,
)

# Log pool events for monitoring
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log successful database connection."""
    logger.debug(f"Database connection established: {dbapi_conn}")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log connection returned to pool."""
    logger.debug("Database connection returned to pool")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checked out from pool."""
    logger.debug("Database connection checked out from pool")


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Get database session with proper cleanup.
    
    Yields:
        SQLAlchemy Session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

