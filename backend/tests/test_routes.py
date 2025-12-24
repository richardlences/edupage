import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from models import User

client = TestClient(app)

# Mock user for dependencies
def mock_get_current_user():
    return User(id=1, edupage_username="testuser", edupage_session_data=b"mockdata")

@pytest.fixture
def override_auth(monkeypatch):
    """Overrides the get_current_user dependency"""
    app.dependency_overrides = {}
    
    # We need to find exactly where get_current_user is imported/used in routers
    from routers.lunches import get_current_user as lunches_get_user
    app.dependency_overrides[lunches_get_user] = mock_get_current_user

    yield
    app.dependency_overrides = {}

@patch("routers.lunches.lunch_cache")
@patch("routers.lunches.get_client")
def test_get_lunches_success(mock_get_client, mock_cache, override_auth):
    # Mock cache miss
    mock_cache.get.return_value = None
    
    # Mock client and response
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
def test_get_lunches_not_logged_in(mock_get_client, mock_cache, override_auth):
    from edupage_internal import NotLoggedInException
    
    mock_cache.get.return_value = None
    mock_get_client.return_value.get_meals_for_date.side_effect = NotLoggedInException()
    
    response = client.get("/api/lunches/?day=2026-01-01", headers={"user-id": "1"})
    
    assert response.status_code == 401
    assert "Session expired" in response.json()['detail']
