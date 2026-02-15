"""Golden example tests for the Users API — update, delete, search."""

import pytest
import requests

BASE_URL = "http://localhost:5000"


@pytest.fixture
def base_url():
    return BASE_URL


@pytest.fixture
def sample_user(base_url):
    """Create a sample user for testing."""
    payload = {"name": "Jane Doe", "email": "jane@example.com", "role": "admin"}
    response = requests.post(f"{base_url}/api/users", json=payload)
    assert response.status_code == 201
    user = response.json()
    yield user
    requests.delete(f"{base_url}/api/users/{user['id']}")


def test_update_user_name(base_url, sample_user):
    """Update only the name field of an existing user."""
    user_id = sample_user["id"]
    payload = {"name": "Jane Updated"}
    response = requests.put(f"{base_url}/api/users/{user_id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Updated"
    assert data["email"] == sample_user["email"]  # unchanged


def test_update_user_role(base_url, sample_user):
    """Update the role of an existing user."""
    user_id = sample_user["id"]
    payload = {"role": "moderator"}
    response = requests.put(f"{base_url}/api/users/{user_id}", json=payload)
    assert response.status_code == 200
    assert response.json()["role"] == "moderator"


def test_update_nonexistent_user(base_url):
    """Attempt to update a user that does not exist."""
    payload = {"name": "Ghost"}
    response = requests.put(f"{base_url}/api/users/99999", json=payload)
    assert response.status_code == 404
    assert "error" in response.json()


def test_delete_user(base_url):
    """Create and then delete a user."""
    # Create
    payload = {"name": "To Delete", "email": "delete@example.com"}
    create_resp = requests.post(f"{base_url}/api/users", json=payload)
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    # Delete
    delete_resp = requests.delete(f"{base_url}/api/users/{user_id}")
    assert delete_resp.status_code == 200

    # Verify gone
    get_resp = requests.get(f"{base_url}/api/users/{user_id}")
    assert get_resp.status_code == 404


def test_delete_nonexistent_user(base_url):
    """Attempt to delete a user that does not exist."""
    response = requests.delete(f"{base_url}/api/users/99999")
    assert response.status_code == 404
    assert "error" in response.json()


def test_search_users_by_name(base_url, sample_user):
    """Search for users by name query."""
    response = requests.get(f"{base_url}/api/users/search", params={"q": "Jane"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(u["name"] == sample_user["name"] for u in data["users"])


def test_search_users_by_email(base_url, sample_user):
    """Search for users by email query."""
    response = requests.get(f"{base_url}/api/users/search", params={"q": "jane@"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_search_users_no_results(base_url):
    """Search with a query that matches no users."""
    response = requests.get(f"{base_url}/api/users/search", params={"q": "zzzznonexistent"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["users"] == []


def test_search_users_missing_query(base_url):
    """Search without providing the required query parameter."""
    response = requests.get(f"{base_url}/api/users/search")
    assert response.status_code == 400
    assert "error" in response.json()
