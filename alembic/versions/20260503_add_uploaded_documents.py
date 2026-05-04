"""Add uploaded_documents table and document source type

Revision ID: 20260503_add_uploaded_documents
Revises: 20260503_add_ai_usage_logs
Create Date: 2026-05-03 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260503_add_uploaded_documents"
down_revision: Union[str, None] = "20260503_add_ai_usage_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'document' value to ai_memory_index.source_type enum
    op.execute(
        "ALTER TABLE ai_memory_index "
        "MODIFY COLUMN source_type ENUM('crs','message','comment','summary','document') NOT NULL"
    )

    # Create uploaded_documents table
    op.create_table(
        "uploaded_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column(
            "status",
            sa.Enum("processing", "ready", "failed", name="documentstatus"),
            nullable=False,
            server_default="processing",
        ),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
    )
    op.create_index("ix_uploaded_documents_id", "uploaded_documents", ["id"])
    op.create_index(
        "ix_uploaded_documents_project_id", "uploaded_documents", ["project_id"]
    )
    op.create_index(
        "ix_uploaded_documents_project_status",
        "uploaded_documents",
        ["project_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_uploaded_documents_project_status", "uploaded_documents")
    op.drop_index("ix_uploaded_documents_project_id", "uploaded_documents")
    op.drop_index("ix_uploaded_documents_id", "uploaded_documents")
    op.drop_table("uploaded_documents")

    op.execute(
        "ALTER TABLE ai_memory_index "
        "MODIFY COLUMN source_type ENUM('crs','message','comment','summary') NOT NULL"
    )
