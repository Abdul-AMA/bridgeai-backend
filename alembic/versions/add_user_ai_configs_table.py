"""Add user_ai_configs table

Revision ID: add_user_ai_configs_table
Revises: 20260207_190521
Create Date: 2026-03-12 14:50:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = "add_user_ai_configs_table"
down_revision: Union[str, None] = "20260207_190521"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create user_ai_configs table for storing user AI provider configurations."""
    op.create_table(
        "user_ai_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "provider",
            sa.Enum(
                "anthropic", "openai", "gemini", "groq", "mistral", name="aiprovider"
            ),
            nullable=False,
        ),
        sa.Column("model_id", sa.String(length=128), nullable=False),
        sa.Column("api_key_encrypted", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            onupdate=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        op.f("ix_user_ai_configs_id"), "user_ai_configs", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_user_ai_configs_user_id"), "user_ai_configs", ["user_id"], unique=True
    )

    op.create_foreign_key(
        "fk_user_ai_configs_user_id",
        "user_ai_configs",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Drop user_ai_configs table."""
    op.drop_constraint(
        "fk_user_ai_configs_user_id", "user_ai_configs", type_="foreignkey"
    )
    op.drop_index(op.f("ix_user_ai_configs_user_id"), table_name="user_ai_configs")
    op.drop_index(op.f("ix_user_ai_configs_id"), table_name="user_ai_configs")
    op.drop_table("user_ai_configs")

    op.execute("DROP TYPE IF EXISTS aiprovider")
