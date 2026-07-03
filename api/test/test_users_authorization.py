from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_current_user

def override_staff_user():
    return {
        "id": 2,
        "name": "Staff User",
        "email": "staff@test.com",
        "role": "STAFF",
        "active": True
    }

def override_admin_user():
    return {
        "id": 1,
        "name": "Admin User",
        "email": "admin@test.com",
        "role": "ADMIN",
        "active": True
    }

def test_staff_cannot_list_user(monkeypatch):
    app.dependency_overrides[get_current_user] = override_staff_user
    client = TestClient(app)

    response = client.get("/users")
    assert response.status_code == 403

    app.dependency_overrides.clear()

def test_staff_cannot_get_user_detail(monkeypatch):
    app.dependency_overrides[get_current_user] = override_staff_user
    client = TestClient(app)

    response = client.get("/users/1")
    assert response.status_code == 403

    app.dependency_overrides.clear()