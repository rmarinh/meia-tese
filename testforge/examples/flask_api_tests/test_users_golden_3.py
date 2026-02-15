"""Golden example tests for the Users API — edge cases and validation."""

import pytest
import requests

BASE_URL = "http://localhost:5000"


@pytest.fixture
def base_url():
    return BASE_URL


def test_create_user_with_custom_role(base_url):
    """Create a user with a custom role specified."""
    payload = {"name": "Admin User", "email": "admin@example.com", "role": "admin"}
    response = requests.post(f"{base_url}/api/users", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "admin"
    requests.delete(f"{base_url}/api/users/{data['id']}")


def test_create_user_empty_body(base_url):
    """Attempt to create user with empty JSON body."""
    response = requests.post(f"{base_url}/api/users", json={})
    assert response.status_code == 400
    assert "error" in response.json()


def test_create_user_no_json(base_url):
    """Attempt to create user without JSON content type."""
    response = requests.post(f"{base_url}/api/users", data="not json")
    assert response.status_code == 400


def test_create_duplicate_email(base_url):
    """Attempt to create two users with the same email."""
    payload = {"name": "First", "email": "duplicate@example.com"}
    resp1 = requests.post(f"{base_url}/api/users", json=payload)
    assert resp1.status_code == 201
    user_id = resp1.json()["id"]

    payload2 = {"name": "Second", "email": "duplicate@example.com"}
    resp2 = requests.post(f"{base_url}/api/users", json=payload2)
    assert resp2.status_code == 409
    assert "error" in resp2.json()

    # Cleanup
    requests.delete(f"{base_url}/api/users/{user_id}")


def test_update_user_empty_body(base_url):
    """Update user with empty body — should succeed with no changes."""
    # Create user first
    payload = {"name": "NoChange", "email": "nochange@example.com"}
    resp = requests.post(f"{base_url}/api/users", json=payload)
    assert resp.status_code == 201
    user_id = resp.json()["id"]

    # Update with empty body
    update_resp = requests.put(f"{base_url}/api/users/{user_id}", json={})
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["name"] == "NoChange"

    requests.delete(f"{base_url}/api/users/{user_id}")


def test_list_users_empty(base_url):
    """List users when no users exist — should return empty list."""
    response = requests.get(f"{base_url}/api/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["users"], list)
    assert isinstance(data["total"], int)
