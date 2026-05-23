"""
Tests for admin log endpoints: category routing, pagination, sanitisation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.admin_audit import AdminAuditLog
from app.models.system_error_log import SystemErrorLog
from app.models.user import User, UserRole
from app.utils.hash import hash_password


def make_admin(db: Session) -> User:
    u = User(
        full_name="Log Admin",
        email="logadmin@example.com",
        password_hash=hash_password("Admin123!"),
        role=UserRole.super_admin,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def admin(db: Session) -> User:
    return make_admin(db)


@pytest.fixture
def admin_token(client: TestClient, admin: User) -> str:
    r = client.post(
        "/api/auth/token",
        data={"username": admin.email, "password": "Admin123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture
def error_log(db: Session) -> SystemErrorLog:
    log = SystemErrorLog(
        error_code="500",
        path="/api/crs/generate",
        method="POST",
        message="LLM timeout after 30s",
        stack_trace="Traceback...",
        user_id=None,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@pytest.fixture
def audit_action_log(db: Session, admin: User) -> AdminAuditLog:
    log = AdminAuditLog(
        actor_id=admin.id,
        actor_email=admin.email,
        action="suspend_user",
        target_type="user",
        target_id=42,
        reason="Test suspension",
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


class TestAdminLogs:
    def test_requires_category_param(self, client: TestClient, admin_token: str):
        r = client.get(
            "/api/admin/logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 422

    def test_invalid_category_returns_422(self, client: TestClient, admin_token: str):
        r = client.get(
            "/api/admin/logs?category=invalid_category",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 422

    def test_audit_trail_category(
        self, client: TestClient, admin_token: str, audit_action_log: AdminAuditLog
    ):
        r = client.get(
            "/api/admin/logs?category=audit_trail",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["category"] == "audit_trail"
        assert "items" in body
        assert body["total"] >= 1

    def test_system_category(
        self, client: TestClient, admin_token: str, error_log: SystemErrorLog
    ):
        r = client.get(
            "/api/admin/logs?category=system",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_pagination_params(self, client: TestClient, admin_token: str):
        r = client.get(
            "/api/admin/logs?category=audit_trail&page=1&page_size=5",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert len(body["items"]) <= 5


class TestAdminErrors:
    def test_errors_endpoint(
        self, client: TestClient, admin_token: str, error_log: SystemErrorLog
    ):
        r = client.get(
            "/api/admin/errors",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["total"] >= 1
        item = body["items"][0]
        assert "message" in item
        # stack_trace must NOT be present in the response
        assert "stack_trace" not in item

    def test_keyword_filter(
        self, client: TestClient, admin_token: str, error_log: SystemErrorLog
    ):
        r = client.get(
            "/api/admin/errors?keyword=timeout",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        messages = [i["message"] for i in r.json()["items"]]
        assert any("timeout" in m.lower() for m in messages)


class TestAdminAudit:
    def test_audit_endpoint_returns_crs_format(self, client: TestClient, admin_token: str):
        r = client.get(
            "/api/admin/audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        assert "items" in r.json()
