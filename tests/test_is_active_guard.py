"""
Tests for is_active suspension guard in get_current_user.

Verifies that a suspended user (is_active=False) receives HTTP 403
on all existing non-admin routes after the suspension flag is set.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.utils.hash import hash_password


@pytest.fixture
def active_ba_user(db: Session) -> User:
    user = User(
        full_name="Active BA",
        email="active_ba@example.com",
        password_hash=hash_password("Active123!"),
        role=UserRole.ba,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def active_token(client: TestClient, active_ba_user: User) -> str:
    resp = client.post(
        "/api/auth/token",
        data={"username": active_ba_user.email, "password": "Active123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


class TestIsActiveGuard:
    def test_active_user_can_access_protected_route(
        self, client: TestClient, active_token: str
    ):
        resp = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {active_token}"},
        )
        assert resp.status_code == 200

    def test_suspended_user_token_returns_403(
        self, client: TestClient, db: Session, active_ba_user: User, active_token: str
    ):
        # Suspend the user directly in the database
        active_ba_user.is_active = False
        db.commit()

        resp = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {active_token}"},
        )
        assert resp.status_code == 403
        assert "suspended" in resp.json().get("detail", "").lower()

    def test_suspended_user_cannot_access_teams(
        self, client: TestClient, db: Session, active_ba_user: User, active_token: str
    ):
        active_ba_user.is_active = False
        db.commit()

        resp = client.get(
            "/api/teams",
            headers={"Authorization": f"Bearer {active_token}"},
        )
        assert resp.status_code == 403

    def test_reactivated_user_can_access_again(
        self, client: TestClient, db: Session, active_ba_user: User, active_token: str
    ):
        # Suspend then reactivate
        active_ba_user.is_active = False
        db.commit()

        suspended_resp = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {active_token}"},
        )
        assert suspended_resp.status_code == 403

        active_ba_user.is_active = True
        db.commit()

        reactivated_resp = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {active_token}"},
        )
        assert reactivated_resp.status_code == 200
