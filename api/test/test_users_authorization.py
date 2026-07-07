from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_current_user
from schemas.users import UserListResponse, UserResponse, UserRole
from datetime import datetime, timezone

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

def test_admin_can_list_users(monkeypatch):
    app.dependency_overrides[get_current_user] = override_admin_user
    client = TestClient(app)

    monkeypatch.setattr(
        "app.routers.users_route.UserService.get_all_users",
        lambda active_only, page, page_size, search: UserListResponse(
            users=[
                UserResponse(
                    id=1,
                    email="admin@test.com",
                    name="Admin User",
                    role=UserRole.ADMIN,
                    active=True,
                    created_at=datetime.now(timezone.utc),
                )
            ],
            total=1,
            page=page,
            page_size=page_size,
        ),
    )

    response = client.get("/users")
    assert response.status_code == 200
    assert response.json()["total"] == 1

    app.dependency_overrides.clear()

def test_admin_can_get_user_detail(monkeypatch):
    app.dependency_overrides[get_current_user] = override_admin_user
    client = TestClient(app)

    monkeypatch.setattr(
        "app.routers.users_route.UserService.get_user_by_id",
        lambda user_id: UserResponse(
            id=user_id,
            email="staff@test.com",
            name="Staff User",
            role=UserRole.STAFF,
            active=True,
            created_at=datetime.now(timezone.utc),
        ),
    )

    response = client.get("/users/2")
    assert response.status_code == 200
    assert response.json()["id"] == 2

    app.dependency_overrides.clear()
