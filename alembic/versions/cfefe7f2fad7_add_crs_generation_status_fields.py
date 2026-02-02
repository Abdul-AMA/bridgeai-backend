"""add_crs_generation_status_fields

Revision ID: cfefe7f2fad7
Revises: ae068e1e14c7
Create Date: 2026-02-01 22:55:06.846278

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cfefe7f2fad7'
down_revision: Union[str, Sequence[str], None] = 'ae068e1e14c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns to sessions table
    # MySQL/MariaDB uses ENUM inline, not as a separate type
    op.add_column('sessions', 
        sa.Column('crs_generation_status', 
                  sa.Enum('idle', 'queued', 'generating', 'complete', 'error', 
                          name='crsgenerationstatus'),
                  nullable=False,
                  server_default='idle')
    )
    op.add_column('sessions', 
        sa.Column('crs_progress_percentage', sa.Integer(), nullable=True, server_default='0')
    )
    op.add_column('sessions', 
        sa.Column('crs_last_generated_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop columns
    op.drop_column('sessions', 'crs_last_generated_at')
    op.drop_column('sessions', 'crs_progress_percentage')
    op.drop_column('sessions', 'crs_generation_status')
