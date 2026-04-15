"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Property


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_live_endpoint(client: TestClient):
    """Test liveness probe endpoint."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


def test_health_ready_endpoint(client: TestClient):
    """Test readiness probe endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "checks" in data
    assert "overall" in data


def test_list_properties_empty(client: TestClient):
    """Test listing properties when none exist."""
    response = client.get("/api/v1/properties")
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_list_properties_with_pagination(client: TestClient, db: Session):
    """Test listing properties with pagination."""
    # Create test properties
    for i in range(5):
        prop = Property(
            address=f"Test St {i}",
            price_text=f"${i*500}/mo",
            price_value=float(i * 500),
            link=f"/property/{i}",
        )
        db.add(prop)
    db.commit()
    
    # Test default limit
    response = client.get("/api/v1/properties")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    
    # Test with limit
    response = client.get("/api/v1/properties?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Test with offset
    response = client.get("/api/v1/properties?limit=2&offset=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_search_properties_invalid_query(client: TestClient):
    """Test search with invalid query."""
    response = client.get("/api/v1/search?q=a")  # Too short
    assert response.status_code == 422  # Validation error


def test_search_properties_valid(client: TestClient, db: Session):
    """Test searching properties."""
    # Create test property
    prop = Property(
        address="123 Main St",
        price_text="$1500/mo",
        price_value=1500.0,
        link="/property/1",
    )
    db.add(prop)
    db.commit()
    
    # Search for it
    response = client.get("/api/v1/search?q=Main")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0


def test_search_with_price_filter(client: TestClient, db: Session):
    """Test searching with price filters."""
    # Create test properties
    for i, price in enumerate([1000, 2000, 3000]):
        prop = Property(
            address=f"Test St {i}",
            price_text=f"${price}/mo",
            price_value=float(price),
            link=f"/property/{i}",
        )
        db.add(prop)
    db.commit()
    
    # Search with price range
    response = client.get("/api/v1/search?q=Test&min_price=1500&max_price=2500")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1  # Only $2000 property


def test_scrape_task_trigger(client: TestClient):
    """Test triggering a scrape task."""
    response = client.post("/api/v1/scrape")
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "queued"


def test_get_task_status(client: TestClient):
    """Test getting task status."""
    # Trigger a task
    response = client.post("/api/v1/scrape")
    task_id = response.json()["task_id"]
    
    # Get status
    response = client.get(f"/api/v1/task/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert "status" in data
