"""merge heads

Revision ID: 0252304dc04b
Revises: 297f5f3a6443, cfefe7f2fad7
Create Date: 2026-02-03 21:18:17.516207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0252304dc04b'
down_revision: Union[str, Sequence[str], None] = ('297f5f3a6443', 'cfefe7f2fad7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
