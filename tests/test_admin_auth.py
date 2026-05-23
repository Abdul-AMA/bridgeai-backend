"""
Tests for super admin authentication guard on admin endpoints.

Verifies:
- GET /api/admin/overview → 401 without JWT
- GET /api/admin/overview → 403 with ba/client JWT
- GET /api/admin/overview → 200 with super_admin JWT
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.utils.hash import hash_password


@pytest.fixture
def super_admin_user(db: Session) -> User:
    user = User(
        full_name="Super Admin",
        email="superadmin@example.com",
        password_hash=hash_password("Admin1234!"),
        role=UserRole.super_admin,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def super_admin_token(client: TestClient, super_admin_user: User) -> str:
    resp = client.post(
        "/api/auth/token",
        data={"username": super_admin_user.email, "password": "Admin1234!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def ba_user_fixture(db: Session) -> User:
    user = User(
        full_name="BA Person",
        email="ba_admin_test@example.com",
        password_hash=hash_password("Ba1234Pass!"),
        role=UserRole.ba,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def ba_token(client: TestClient, ba_user_fixture: User) -> str:
    resp = client.post(
        "/api/auth/token",
        data={"username": ba_user_fixture.email, "password": "Ba1234Pass!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def client_user_fixture(db: Session) -> User:
    user = User(
        full_name="Regular Client",
        email="client_admin_test@example.com",
        password_hash=hash_password("Client123!"),
        role=UserRole.client,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def client_token(client: TestClient, client_user_fixture: User) -> str:
    resp = client.post(
        "/api/auth/token",
        data={"username": client_user_fixture.email, "password": "Client123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


class TestAdminOverviewAuth:
    def test_no_jwt_returns_401(self, client: TestClient):
        resp = client.get("/api/admin/overview")
        assert resp.status_code == 401

    def test_ba_jwt_returns_403(self, client: TestClient, ba_token: str):
        resp = client.get(
            "/api/admin/overview",
            headers={"Authorization": f"Bearer {ba_token}"},
        )
        assert resp.status_code == 403

    def test_client_jwt_returns_403(self, client: TestClient, client_token: str):
        resp = client.get(
            "/api/admin/overview",
            headers={"Authorization": f"Bearer {client_token}"},
        )
        assert resp.status_code == 403

    def test_super_admin_jwt_returns_200(
        self, client: TestClient, super_admin_token: str
    ):
        resp = client.get(
            "/api/admin/overview",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert resp.status_code == 200
