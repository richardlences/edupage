import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from models import User

client = TestClient(app)

# Mock user for dependencies
def mock_get_current_user():
    return User(id=1, edupage_username="testuser", edupage_session_data=b"mockdata")

def mock_get_db():
    db = MagicMock()
    yield db

@pytest.fixture
def override_auth_and_db():
    """Overrides dependencies for auth and db"""
    app.dependency_overrides = {}
    
    from routers.lunches import get_current_user, get_db
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_db] = mock_get_db

    yield
    app.dependency_overrides = {}

@patch("routers.lunches.lunch_cache")
@patch("routers.lunches.get_client")
def test_get_lunches_success(mock_get_client, mock_cache, override_auth_and_db):
    # Mock cache miss
    mock_cache.get.return_value = None
    
    # Mock database session
    mock_db = next(mock_get_db())
    # Mock the chain db.query(...).filter(...).scalar() or .all()
    # We can just make it return None/empty for ratings/photos
    mock_db.query.return_value.filter.return_value.scalar.return_value = None
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_edupage_client = MagicMock()
    mock_get_client.return_value = mock_edupage_client
    
    # Mock return from get_meals_for_date
    mock_edupage_client.get_meals_for_date.return_value = {
        "2026-01-01": {
            "date": "2026-01-01",
            "menus": [{"name": "Tasty Lunch", "number": "1"}],
            "ordered_meal": "A",
            "can_be_changed_until": None
        }
    }

    # Make request
    response = client.get("/api/lunches/?day=2026-01-01", headers={"user-id": "1"})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['name'] == "Tasty Lunch"
    assert data[0]['is_ordered'] is True # Meal A is index 0 -> ordered

@patch("routers.lunches.lunch_cache")
@patch("routers.lunches.get_client")
def test_get_lunches_not_logged_in(mock_get_client, mock_cache, override_auth_and_db):
    from edupage_internal import NotLoggedInException
    
    mock_cache.get.return_value = None
    mock_get_client.return_value.get_meals_for_date.side_effect = NotLoggedInException()
    
    response = client.get("/api/lunches/?day=2026-01-01", headers={"user-id": "1"})
    
    assert response.status_code == 401
    assert "Session expired" in response.json()['detail']
