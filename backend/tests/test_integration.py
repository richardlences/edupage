import pytest
import os
from edupage_internal import EdupageClient

@pytest.mark.integration
def test_real_login_and_fetch():
    username = os.environ.get("EDUPAGE_USERNAME")
    password = os.environ.get("EDUPAGE_PASSWORD")
    subdomain = os.environ.get("EDUPAGE_SUBDOMAIN")
    
    if not (username and password and subdomain):
        pytest.skip("Missing Edupage credentials in environment")
        
    client = EdupageClient()
    client.login(username, password, subdomain)
    
    assert client.is_logged_in
    assert client.username == username
    
    # Try fetching meals (lightweight ping)
    from datetime import date
    try:
        meals = client.get_meals_for_date(date.today())
        # Even if empty, it shouldn't raise exception
        assert isinstance(meals, dict)
    except Exception as e:
        pytest.fail(f"Fetching meals failed: {e}")
