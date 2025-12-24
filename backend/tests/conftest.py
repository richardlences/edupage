import pytest
import os
import sys
import json
from datetime import date
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from edupage_internal import EdupageClient

@pytest.fixture
def mock_edupage_html():
    return """
    <html>
        <body>
            <script>
                var edupageData = {
                    "myschool": {
                        "novyListok": {
                             "addInfo": { "stravnikid": "12345" },
                             "2026-01-08": {
                                 "2": {
                                     "evidencia": { "stav": "B", "obj": "A" },
                                     "rows": [
                                         { "menusStr": "1", "nazov": "Meal 1" },
                                         { "menusStr": "2", "nazov": "Meal 2" }
                                     ],
                                     "zmen_do": "2026-01-07T14:00:00",
                                     "isCooking": true
                                 }
                             }
                        }
                    }
                };
            </script>
        </body>
    </html>
    """

@pytest.fixture
def mock_client():
    client = EdupageClient()
    client.subdomain = "myschool"
    client.is_logged_in = True
    return client
