"""Add RTM tables

Revision ID: 20260510_add_rtm_tables
Revises: 20260503_add_ctx_summaries
Create Date: 2026-05-10 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260510_add_rtm_tables"
down_revision: Union[str, None] = "20260503_add_ctx_summaries"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. requirements table
    op.create_table(
        "requirements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("req_id", sa.String(20), nullable=False),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id"),
            nullable=False,
        ),
        sa.Column(
            "crs_document_id",
            sa.Integer(),
            sa.ForeignKey("crs_documents.id"),
            nullable=False,
        ),
        sa.Column("section", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("full_text", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "archived", name="requirementstatus"),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "req_id", name="uq_requirements_project_req_id"),
        mysql_engine="InnoDB",
    )
    op.create_index("ix_requirements_id", "requirements", ["id"])
    op.create_index(
        "ix_requirements_project_status",
        "requirements",
        ["project_id", "status"],
    )

    # 2. traceability_links table
    op.create_table(
        "traceability_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "requirement_id",
            sa.Integer(),
            sa.ForeignKey("requirements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_type",
            sa.Enum("chat_message", "document", name="sourcetype"),
            nullable=False,
        ),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column(
            "is_auto_generated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
    )
    op.create_index("ix_traceability_links_id", "traceability_links", ["id"])
    op.create_index(
        "ix_traceability_links_requirement_id",
        "traceability_links",
        ["requirement_id"],
    )

    # 3. test_cases table
    op.create_table(
        "test_cases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "requirement_id",
            sa.Integer(),
            sa.ForeignKey("requirements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("preconditions", sa.Text(), nullable=True),
        sa.Column("steps", sa.Text(), nullable=False),
        sa.Column("expected_result", sa.Text(), nullable=False),
        sa.Column(
            "is_auto_generated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "status",
            sa.Enum("active", "archived", name="testcasestatus"),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
    )
    op.create_index("ix_test_cases_id", "test_cases", ["id"])
    op.create_index(
        "ix_test_cases_requirement_id", "test_cases", ["requirement_id"]
    )

    # 4. rtm_status table (one row per project)
    op.create_table(
        "rtm_status",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "is_refreshing",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("last_refreshed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_trigger",
            sa.Enum(
                "save", "status_change", "draft", "manual", name="rtmtrigger"
            ),
            nullable=True,
        ),
        sa.Column(
            "requirement_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "unverified_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "untested_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_rtm_status_project_id"),
        mysql_engine="InnoDB",
    )
    op.create_index("ix_rtm_status_id", "rtm_status", ["id"])
    op.create_index(
        "ix_rtm_status_project_id", "rtm_status", ["project_id"], unique=True
    )

    # 5. Alter comments: make crs_id nullable, add requirement_id FK
    op.alter_column("comments", "crs_id", existing_type=sa.Integer(), nullable=True)
    op.add_column(
        "comments",
        sa.Column(
            "requirement_id",
            sa.Integer(),
            sa.ForeignKey("requirements.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_comments_requirement_id", "comments", ["requirement_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_comments_requirement_id", table_name="comments")
    op.drop_column("comments", "requirement_id")
    op.alter_column("comments", "crs_id", existing_type=sa.Integer(), nullable=False)

    op.drop_index("ix_rtm_status_project_id", table_name="rtm_status")
    op.drop_index("ix_rtm_status_id", table_name="rtm_status")
    op.drop_table("rtm_status")
    sa.Enum(name="rtmtrigger").drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_test_cases_requirement_id", table_name="test_cases")
    op.drop_index("ix_test_cases_id", table_name="test_cases")
    op.drop_table("test_cases")
    sa.Enum(name="testcasestatus").drop(op.get_bind(), checkfirst=True)

    op.drop_index(
        "ix_traceability_links_requirement_id", table_name="traceability_links"
    )
    op.drop_index("ix_traceability_links_id", table_name="traceability_links")
    op.drop_table("traceability_links")
    sa.Enum(name="sourcetype").drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_requirements_project_status", table_name="requirements")
    op.drop_index("ix_requirements_id", table_name="requirements")
    op.drop_table("requirements")
    sa.Enum(name="requirementstatus").drop(op.get_bind(), checkfirst=True)
