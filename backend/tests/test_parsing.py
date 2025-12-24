import pytest
from datetime import date
from unittest.mock import MagicMock
from edupage_internal import EdupageClient
def test_parse_single_meal_ordered_b():
    client = EdupageClient()
    
    # Mock data representing the "future lunch bug" scenario
    # Status is 'B', obj is 'A'. Should be parsed as 'B'.
    raw_data = {
        "isCooking": True,
        "evidencia": { "stav": "B", "obj": "A" },
        "rows": [
            { "menusStr": "1", "nazov": "Meal 1" },
            { "menusStr": "2", "nazov": "Meal 2" }
        ],
        "zmen_do": "2026-01-07T14:00:00"
    }
    
    result = client._parse_single_meal(raw_data, "12345", "2026-01-08", "2")
    
    assert result is not None
    assert result['ordered_meal'] == "B"
    assert len(result['menus']) == 2
    assert result['menus'][0]['name'] == "Meal 1"

def test_parse_single_meal_ordered_v():
    client = EdupageClient()
    
    # Standard scenario
    raw_data = {
        "isCooking": True,
        "evidencia": { "stav": "V", "obj": "C" },
        "rows": [],
        "zmen_do": "2026-01-07T14:00:00"
    }
    
    result = client._parse_single_meal(raw_data, "12345", "2026-01-08", "2")
    
    assert result['ordered_meal'] == "C"

def test_parse_single_meal_cancelled():
    client = EdupageClient()
    
    # Cancelled scenario
    raw_data = {
        "isCooking": True,
        "evidencia": { "stav": "X", "obj": "A" },
        "rows": [],
        "zmen_do": "2026-01-07T14:00:00"
    }
    
    result = client._parse_single_meal(raw_data, "12345", "2026-01-08", "2")
    
    assert result['ordered_meal'] is None
