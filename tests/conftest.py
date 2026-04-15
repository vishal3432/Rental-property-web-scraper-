"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.db.session import Base, get_db


# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a test database."""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session):
    """Create a test client."""
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_html():
    """Sample HTML for parser testing."""
    return """
    <html>
        <div class="StyledPropertyCardDataWrapper">
            <a href="/property/1">Link 1</a>
            <address>123 Main St, City, State 12345</address>
        </div>
        <div class="PropertyCardWrapper">
            <span>$1,500/mo</span>
        </div>
        <div class="StyledPropertyCardDataWrapper">
            <a href="/property/2">Link 2</a>
            <address>456 Oak Ave, City, State 67890</address>
        </div>
        <div class="PropertyCardWrapper">
            <span>$2,000/mo</span>
        </div>
    </html>
    """
