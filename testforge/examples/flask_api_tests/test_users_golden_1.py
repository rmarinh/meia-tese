"""Golden example tests for the Users API — CRUD operations."""

import pytest
import requests

BASE_URL = "http://localhost:5000"


@pytest.fixture
def base_url():
    """Base URL for the API."""
    return BASE_URL


@pytest.fixture
def created_user(base_url):
    """Create a user and return its data. Clean up after test."""
    payload = {"name": "Test User", "email": "test@example.com", "role": "user"}
    response = requests.post(f"{base_url}/api/users", json=payload)
    assert response.status_code == 201
    user = response.json()
    yield user
    # Cleanup
    requests.delete(f"{base_url}/api/users/{user['id']}")


def test_health_check(base_url):
    """Verify the health endpoint returns ok status."""
    response = requests.get(f"{base_url}/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_create_user(base_url):
    """Create a new user with valid data."""
    payload = {"name": "Alice Smith", "email": "alice@example.com"}
    response = requests.post(f"{base_url}/api/users", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alice Smith"
    assert data["email"] == "alice@example.com"
    assert data["role"] == "user"  # default role
    assert "id" in data

    # Cleanup
    requests.delete(f"{base_url}/api/users/{data['id']}")


def test_create_user_missing_name(base_url):
    """Attempt to create user without name field."""
    payload = {"email": "noname@example.com"}
    response = requests.post(f"{base_url}/api/users", json=payload)
    assert response.status_code == 400
    assert "error" in response.json()


def test_create_user_missing_email(base_url):
    """Attempt to create user without email field."""
    payload = {"name": "No Email"}
    response = requests.post(f"{base_url}/api/users", json=payload)
    assert response.status_code == 400
    assert "error" in response.json()


def test_get_user(base_url, created_user):
    """Retrieve a user by ID."""
    user_id = created_user["id"]
    response = requests.get(f"{base_url}/api/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["name"] == created_user["name"]
    assert data["email"] == created_user["email"]


def test_get_nonexistent_user(base_url):
    """Attempt to retrieve a user that does not exist."""
    response = requests.get(f"{base_url}/api/users/99999")
    assert response.status_code == 404
    assert "error" in response.json()


def test_list_users(base_url, created_user):
    """List all users and verify the created user is included."""
    response = requests.get(f"{base_url}/api/users")
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "total" in data
    assert data["total"] >= 1
    user_ids = [u["id"] for u in data["users"]]
    assert created_user["id"] in user_ids
