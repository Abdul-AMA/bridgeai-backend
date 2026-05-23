"""
Tests for GET/PATCH admin user endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.utils.hash import hash_password


def make_user(db: Session, email: str, role: UserRole, is_active: bool = True) -> User:
    u = User(
        full_name="Test User",
        email=email,
        password_hash=hash_password("Pass1234!"),
        role=role,
        is_active=is_active,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def admin(db: Session) -> User:
    return make_user(db, "admin@example.com", UserRole.super_admin)


@pytest.fixture
def admin_token(client: TestClient, admin: User) -> str:
    r = client.post(
        "/api/auth/token",
        data={"username": admin.email, "password": "Pass1234!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture
def regular_user(db: Session) -> User:
    return make_user(db, "user@example.com", UserRole.ba)


class TestAdminUserList:
    def test_list_returns_users(self, client: TestClient, admin_token: str, regular_user: User):
        r = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert body["total"] >= 1

    def test_search_by_email(self, client: TestClient, admin_token: str, regular_user: User):
        r = client.get(
            f"/api/admin/users?search={regular_user.email}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        emails = [u["email"] for u in r.json()["items"]]
        assert regular_user.email in emails

    def test_filter_by_role(self, client: TestClient, admin_token: str, regular_user: User):
        r = client.get(
            "/api/admin/users?role=ba",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["role"] == "ba"

    def test_filter_suspended(self, client: TestClient, db: Session, admin_token: str):
        make_user(db, "suspended@example.com", UserRole.client, is_active=False)
        r = client.get(
            "/api/admin/users?status=suspended",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["is_active"] is False


class TestAdminUserDetail:
    def test_returns_user_detail(self, client: TestClient, admin_token: str, regular_user: User):
        r = client.get(
            f"/api/admin/users/{regular_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == regular_user.id
        assert body["email"] == regular_user.email
        assert "team_memberships" in body

    def test_returns_404_for_missing_user(self, client: TestClient, admin_token: str):
        r = client.get(
            "/api/admin/users/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 404


class TestAdminUserSuspend:
    def test_suspend_user(self, client: TestClient, admin_token: str, regular_user: User):
        r = client.patch(
            f"/api/admin/users/{regular_user.id}/status",
            json={"action": "suspend", "reason": "Policy violation"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["is_active"] is False
        assert body["suspension_reason"] == "Policy violation"

    def test_suspend_requires_reason(self, client: TestClient, admin_token: str, regular_user: User):
        r = client.patch(
            f"/api/admin/users/{regular_user.id}/status",
            json={"action": "suspend"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code in (400, 422)

    def test_suspend_idempotency(self, client: TestClient, admin_token: str, regular_user: User):
        client.patch(
            f"/api/admin/users/{regular_user.id}/status",
            json={"action": "suspend", "reason": "First"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        r = client.patch(
            f"/api/admin/users/{regular_user.id}/status",
            json={"action": "suspend", "reason": "Second"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 400

    def test_self_suspension_blocked(self, client: TestClient, admin_token: str, admin: User):
        r = client.patch(
            f"/api/admin/users/{admin.id}/status",
            json={"action": "suspend", "reason": "Testing self"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 403

    def test_reactivate_user(
        self, client: TestClient, db: Session, admin_token: str, regular_user: User
    ):
        regular_user.is_active = False
        db.commit()

        r = client.patch(
            f"/api/admin/users/{regular_user.id}/status",
            json={"action": "reactivate"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        assert r.json()["is_active"] is True


class TestAdminUserRoleChange:
    def test_change_role_ba_to_client(
        self, client: TestClient, admin_token: str, regular_user: User
    ):
        r = client.patch(
            f"/api/admin/users/{regular_user.id}/role",
            json={"role": "client"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        assert r.json()["role"] == "client"

    def test_cannot_set_super_admin_role(
        self, client: TestClient, admin_token: str, regular_user: User
    ):
        r = client.patch(
            f"/api/admin/users/{regular_user.id}/role",
            json={"role": "super_admin"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code in (400, 422)
