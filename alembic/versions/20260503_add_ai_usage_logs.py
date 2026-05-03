"""Add ai_usage_logs table

Revision ID: 20260503_add_ai_usage_logs
Revises: add_user_ai_configs_table
Create Date: 2026-05-03 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260503_add_ai_usage_logs"
down_revision: Union[str, None] = "add_user_ai_configs_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_usage_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.Integer(), nullable=True),
        sa.Column("node_type", sa.String(64), nullable=False),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False, server_default="anthropic"),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_usage_logs_id", "ai_usage_logs", ["id"])
    op.create_index("ix_ai_usage_logs_user_id", "ai_usage_logs", ["user_id"])
    op.create_index("ix_ai_usage_logs_project_id", "ai_usage_logs", ["project_id"])
    op.create_index("ix_ai_usage_logs_session_id", "ai_usage_logs", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_usage_logs_session_id", table_name="ai_usage_logs")
    op.drop_index("ix_ai_usage_logs_project_id", table_name="ai_usage_logs")
    op.drop_index("ix_ai_usage_logs_user_id", table_name="ai_usage_logs")
    op.drop_index("ix_ai_usage_logs_id", table_name="ai_usage_logs")
    op.drop_table("ai_usage_logs")
