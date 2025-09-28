import pytest
from syqlorix import Syqlorix, body, h1

# A simple app for testing purposes
app = Syqlorix()

@app.route('/')
def home(request):
    return h1("Welcome!")

@pytest.fixture
def client():
    """Create a test client for the Syqlorix app."""
    return app.test_client()

def test_home_page(client):
    """Test the home page."""
    response = client.get('/')
    assert response.status_code == 200
    assert "<h1>\n      Welcome!\n    </h1>" in response.text
