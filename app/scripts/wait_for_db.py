"""
Database connection validation script for production deployment.
Ensures database is ready before starting the application.
"""

import sys
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def wait_for_database(
    database_url: str,
    max_attempts: int = 30,
    delay_seconds: float = 2.0,
    timeout: int = 5,
) -> bool:
    """
    Wait for database to be available.
    
    Args:
        database_url: Database connection URL
        max_attempts: Maximum number of connection attempts
        delay_seconds: Delay between attempts in seconds
        timeout: Connection timeout in seconds
        
    Returns:
        True if database is ready, False otherwise
    """
    attempt = 0
    
    while attempt < max_attempts:
        try:
            logger.info(f"Attempting database connection (attempt {attempt + 1}/{max_attempts})...")
            
            engine = create_engine(
                database_url,
                connect_args={"timeout": timeout},
                echo=False,
            )
            
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                logger.info("✓ Database connection successful!")
                return True
                
        except (OperationalError, Exception) as e:
            attempt += 1
            if attempt < max_attempts:
                logger.warning(
                    f"✗ Database not ready (attempt {attempt}/{max_attempts}). "
                    f"Retrying in {delay_seconds}s... Error: {str(e)[:100]}"
                )
                time.sleep(delay_seconds)
            else:
                logger.error(f"✗ Database connection failed after {max_attempts} attempts")
                logger.error(f"Error: {str(e)}")
                return False
    
    return False


if __name__ == "__main__":
    from app.core.config import get_settings
    
    settings = get_settings()
    logger.info(f"Checking database: {settings.database_url}")
    
    if wait_for_database(settings.database_url):
        logger.info("✓ Database is ready. Application can start.")
        sys.exit(0)
    else:
        logger.error("✗ Database is not ready. Aborting startup.")
        sys.exit(1)
