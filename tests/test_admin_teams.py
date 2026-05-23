"""
Tests for GET/PATCH admin team endpoints and team suspension enforcement.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.team import Team, TeamMember, TeamRole, TeamStatus
from app.models.user import User, UserRole
from app.utils.hash import hash_password


def make_user(db: Session, email: str, role: UserRole) -> User:
    u = User(
        full_name="Test",
        email=email,
        password_hash=hash_password("Pass1234!"),
        role=role,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def make_team(db: Session, creator: User, name: str = "Test Team") -> Team:
    t = Team(name=name, created_by=creator.id, status=TeamStatus.active)
    db.add(t)
    db.commit()
    db.refresh(t)
    m = TeamMember(team_id=t.id, user_id=creator.id, role=TeamRole.ba, is_active=True)
    db.add(m)
    db.commit()
    return t


@pytest.fixture
def admin(db: Session) -> User:
    return make_user(db, "teamadmin@example.com", UserRole.super_admin)


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
def team_owner(db: Session) -> User:
    return make_user(db, "owner@example.com", UserRole.ba)


@pytest.fixture
def team(db: Session, team_owner: User) -> Team:
    return make_team(db, team_owner)


class TestAdminTeamList:
    def test_list_returns_teams(self, client: TestClient, admin_token: str, team: Team):
        r = client.get("/api/admin/teams", headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_filter_by_status(self, client: TestClient, db: Session, admin_token: str, team: Team):
        team.status = TeamStatus.suspended
        db.commit()

        r = client.get(
            "/api/admin/teams?status=suspended",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["status"] == "suspended"

    def test_search_by_name(self, client: TestClient, admin_token: str, team: Team):
        r = client.get(
            f"/api/admin/teams?search={team.name}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        names = [t["name"] for t in r.json()["items"]]
        assert team.name in names


class TestAdminTeamDetail:
    def test_returns_team_detail(self, client: TestClient, admin_token: str, team: Team):
        r = client.get(
            f"/api/admin/teams/{team.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == team.id
        assert "members" in body

    def test_returns_404_for_missing(self, client: TestClient, admin_token: str):
        r = client.get(
            "/api/admin/teams/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 404


class TestAdminTeamSuspend:
    def test_suspend_team(self, client: TestClient, admin_token: str, team: Team):
        r = client.patch(
            f"/api/admin/teams/{team.id}/status",
            json={"action": "suspend", "reason": "Invoice overdue"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "suspended"

    def test_suspend_requires_reason(self, client: TestClient, admin_token: str, team: Team):
        r = client.patch(
            f"/api/admin/teams/{team.id}/status",
            json={"action": "suspend"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code in (400, 422)

    def test_suspend_idempotency(self, client: TestClient, db: Session, admin_token: str, team: Team):
        team.status = TeamStatus.suspended
        db.commit()
        r = client.patch(
            f"/api/admin/teams/{team.id}/status",
            json={"action": "suspend", "reason": "Again"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 400

    def test_reactivate_team(self, client: TestClient, db: Session, admin_token: str, team: Team):
        team.status = TeamStatus.suspended
        team.suspended_by = 1
        team.suspension_reason = "test"
        db.commit()

        r = client.patch(
            f"/api/admin/teams/{team.id}/status",
            json={"action": "reactivate"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "active"

    def test_suspended_team_blocks_member_access(
        self, client: TestClient, db: Session, team_owner: User, team: Team
    ):
        # Get a token for the team owner
        r = client.post(
            "/api/auth/token",
            data={"username": team_owner.email, "password": "Pass1234!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert r.status_code == 200
        owner_token = r.json()["access_token"]

        # Suspend the team
        team.status = TeamStatus.suspended
        db.commit()

        # Team member should get 403 on team-scoped route
        r2 = client.get(
            f"/api/teams/{team.id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert r2.status_code == 403
