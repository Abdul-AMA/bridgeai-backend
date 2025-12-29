"""add_crs_document_id_to_sessions

Revision ID: 7881c2352291
Revises: 98e4ce3892b6
Create Date: 2025-12-29 00:33:16.718032

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7881c2352291'
down_revision: Union[str, Sequence[str], None] = '98e4ce3892b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add crs_document_id column to sessions table
    op.add_column('sessions', sa.Column('crs_document_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_sessions_crs_document_id', 'sessions', 'crs_documents', ['crs_document_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_sessions_crs_document_id', 'sessions', ['crs_document_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_sessions_crs_document_id', 'sessions')
    op.drop_constraint('fk_sessions_crs_document_id', 'sessions', type_='foreignkey')
    op.drop_column('sessions', 'crs_document_id')
