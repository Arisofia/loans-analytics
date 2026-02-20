import pytest
import requests

# Example backend integration test
def test_get_users():
    response = requests.get("http://localhost:8000/users")
    assert response.status_code == 200
    assert len(response.json()) > 0
