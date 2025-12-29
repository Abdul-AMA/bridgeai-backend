"""add_rejection_reason_and_reviewed_at_to_crs

Revision ID: 93c7feaf3e69
Revises: 16041c546c69
Create Date: 2025-12-28 17:39:21.560660

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93c7feaf3e69'
down_revision: Union[str, Sequence[str], None] = '16041c546c69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('crs_documents', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('crs_documents', sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('crs_documents', 'reviewed_at')
    op.drop_column('crs_documents', 'rejection_reason')
