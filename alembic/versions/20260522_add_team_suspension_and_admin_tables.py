"""add team suspension fields, admin_audit_logs, system_error_logs

Revision ID: 20260522_team_admin_tables
Revises: 20260522_super_admin_user
Create Date: 2026-05-22
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260522_team_admin_tables"
down_revision: Union[str, None] = "20260522_super_admin_user"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add suspended to teamstatus enum
    op.execute("ALTER TABLE teams MODIFY COLUMN status ENUM('active', 'inactive', 'archived', 'suspended') NOT NULL DEFAULT 'active'")

    # Add suspension fields to teams
    op.add_column("teams", sa.Column("suspended_by", sa.Integer(), nullable=True))
    op.add_column("teams", sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("teams", sa.Column("suspension_reason", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_teams_suspended_by", "teams", "users", ["suspended_by"], ["id"], ondelete="SET NULL"
    )

    # Create admin_audit_logs table
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("actor_email", sa.String(256), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("before_state", sa.Text(), nullable=True),
        sa.Column("after_state", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        mysql_engine="InnoDB",
    )
    op.create_index("ix_admin_audit_logs_actor_id", "admin_audit_logs", ["actor_id"])
    op.create_index("ix_admin_audit_logs_action", "admin_audit_logs", ["action"])
    op.create_index("ix_admin_audit_logs_created_at", "admin_audit_logs", ["created_at"])

    # Create system_error_logs table
    op.create_table(
        "system_error_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("error_code", sa.String(64), nullable=False),
        sa.Column("path", sa.String(512), nullable=False),
        sa.Column("method", sa.String(16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("stack_trace", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        mysql_engine="InnoDB",
    )
    op.create_index("ix_system_error_logs_error_code", "system_error_logs", ["error_code"])
    op.create_index("ix_system_error_logs_created_at", "system_error_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_system_error_logs_created_at", table_name="system_error_logs")
    op.drop_index("ix_system_error_logs_error_code", table_name="system_error_logs")
    op.drop_table("system_error_logs")
    op.drop_index("ix_admin_audit_logs_created_at", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_action", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_actor_id", table_name="admin_audit_logs")
    op.drop_table("admin_audit_logs")
    op.drop_constraint("fk_teams_suspended_by", "teams", type_="foreignkey")
    op.drop_column("teams", "suspension_reason")
    op.drop_column("teams", "suspended_at")
    op.drop_column("teams", "suspended_by")
    op.execute("ALTER TABLE teams MODIFY COLUMN status ENUM('active', 'inactive', 'archived') NOT NULL DEFAULT 'active'")
