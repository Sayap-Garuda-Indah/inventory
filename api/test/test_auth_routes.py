from fastapi.testclient import TestClient

from app.main import app


def test_auth_register_route_is_not_public():
    client = TestClient(app)

    response = client.post(
        "/auth/register",
        json={
            "name": "Public User",
            "email": "public@example.com",
            "password": "PublicPassword123",
        },
    )

    assert response.status_code == 404
