"""add super_admin role and user suspension fields

Revision ID: 20260522_super_admin_user
Revises: 20260510_add_rtm_tables
Create Date: 2026-05-22
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260522_super_admin_user"
down_revision: Union[str, None] = "20260510_add_rtm_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add super_admin to userrole enum (MySQL requires recreating the column)
    op.execute("ALTER TABLE users MODIFY COLUMN role ENUM('client', 'ba', 'super_admin') NULL")

    # Add suspension fields to users
    op.add_column("users", sa.Column("suspended_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("users", sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("suspension_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "suspension_reason")
    op.drop_column("users", "suspended_at")
    op.drop_column("users", "suspended_by")
    op.execute("ALTER TABLE users MODIFY COLUMN role ENUM('client', 'ba') NULL")
