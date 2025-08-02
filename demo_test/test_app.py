import pytest
from app import doc # Import the doc object from our application

@pytest.fixture
def client():
    """Creates a test client fixture for our tests to use."""
    return doc.test_client()

def test_home_route(client):
    """Test the home page."""
    response = client.get('/')
    assert response.status_code == 200
    assert "Welcome Home!" in response.text

def test_dynamic_route(client):
    """Test a route with a path parameter."""
    response = client.get('/user/Benjo')
    assert response.status_code == 200
    assert "Profile of Benjo" in response.text

def test_post_request(client):
    """Test making a POST request with form data."""
    response = client.post('/login', data={'username': 'Syqlorix'})
    assert response.status_code == 200
    assert "Logged in as Syqlorix" in response.text

def test_redirect_route(client):
    """Test that a route correctly redirects."""
    response = client.get('/old-path')
    assert response.status_code == 302
    assert response.headers['Location'] == '/user/redirected'

def test_404_not_found(client):
    """Test that a non-existent page returns a 404."""
    response = client.get('/this-page-does-not-exist')
    assert response.status_code == 404
    assert "Not Found" in response.text