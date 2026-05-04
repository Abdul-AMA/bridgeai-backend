"""Add project_context_summaries table

Revision ID: 20260503_add_ctx_summaries
Revises: 20260503_add_uploaded_documents
Create Date: 2026-05-03 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260503_add_ctx_summaries"
down_revision: Union[str, None] = "20260503_add_uploaded_documents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_context_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_generating",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "last_trigger",
            sa.Enum("document", "chat", "manual", name="triggertype"),
            nullable=False,
            server_default="manual",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", name="uq_project_context_summaries_project_id"
        ),
        mysql_engine="InnoDB",
    )
    op.create_index(
        "ix_project_context_summaries_id",
        "project_context_summaries",
        ["id"],
    )
    op.create_index(
        "ix_project_context_summaries_project_id",
        "project_context_summaries",
        ["project_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_project_context_summaries_project_id",
        table_name="project_context_summaries",
    )
    op.drop_index(
        "ix_project_context_summaries_id",
        table_name="project_context_summaries",
    )
    op.drop_table("project_context_summaries")
    sa.Enum(name="triggertype").drop(op.get_bind(), checkfirst=True)
