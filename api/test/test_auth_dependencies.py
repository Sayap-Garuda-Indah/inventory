from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.dependencies import get_current_user


def make_request(path: str = "/auth/me"):
    return SimpleNamespace(
        url=SimpleNamespace(path=path),
        client=SimpleNamespace(host="127.0.0.1"),
    )


def make_credentials(token: str = "token"):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_get_current_user_missing_token_returns_401():
    with pytest.raises(HTTPException) as exc:
        get_current_user(make_request(), None)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid or missing token"
    assert exc.value.headers == {"WWW-Authenticate": "Bearer"}


def test_get_current_user_invalid_token_returns_401(monkeypatch):
    monkeypatch.setattr("app.dependencies.verify_access_token", lambda token: (_ for _ in ()).throw(ValueError("bad token")))

    with pytest.raises(HTTPException) as exc:
        get_current_user(make_request(), make_credentials())

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid or expired token"
    assert exc.value.headers == {"WWW-Authenticate": "Bearer"}


def test_get_current_user_invalid_payload_returns_401(monkeypatch):
    monkeypatch.setattr("app.dependencies.verify_access_token", lambda token: {"sub": "user@example.com"})

    with pytest.raises(HTTPException) as exc:
        get_current_user(make_request(), make_credentials())

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token payload"
    assert exc.value.headers == {"WWW-Authenticate": "Bearer"}


def test_get_current_user_missing_user_returns_404(monkeypatch):
    monkeypatch.setattr("app.dependencies.verify_access_token", lambda token: {"user_id": 99})
    monkeypatch.setattr("app.dependencies.UserRepository.get_by_id", lambda user_id: None)

    with pytest.raises(HTTPException) as exc:
        get_current_user(make_request(), make_credentials())

    assert exc.value.status_code == 404
    assert exc.value.detail == "User not found"


def test_get_current_user_inactive_user_returns_403(monkeypatch):
    monkeypatch.setattr("app.dependencies.verify_access_token", lambda token: {"user_id": 7})
    monkeypatch.setattr(
        "app.dependencies.UserRepository.get_by_id",
        lambda user_id: {
            "id": user_id,
            "email": "inactive@example.com",
            "name": "Inactive User",
            "role": "STAFF",
            "active": False,
        },
    )

    with pytest.raises(HTTPException) as exc:
        get_current_user(make_request(), make_credentials())

    assert exc.value.status_code == 403
    assert exc.value.detail == "User inactive or not found"
