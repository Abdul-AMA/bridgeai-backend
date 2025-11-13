"""add teams and team members tables

Revision ID: a1b2c3d4e5f6
Revises: 531baa9737e9
Create Date: 2025-11-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '531baa9737e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    # Create ENUM types for teams
    team_role = sa.Enum('owner', 'admin', 'member', 'viewer', name='teamrole')
    team_status = sa.Enum('active', 'inactive', 'archived', name='teamstatus')

    team_role.create(bind, checkfirst=True)
    team_status.create(bind, checkfirst=True)

    # Create teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', team_status, nullable=True, server_default='active'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_teams_id', 'teams', ['id'], unique=False)

    # Create team_members table
    op.create_table(
        'team_members',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('role', team_role, nullable=True, server_default='member'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('team_id', 'user_id', name='unique_team_user'),
    )
    op.create_index('ix_team_members_id', 'team_members', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    # Drop indexes and tables in reverse order
    op.drop_index('ix_team_members_id', table_name='team_members')
    op.drop_table('team_members')

    op.drop_index('ix_teams_id', table_name='teams')
    op.drop_table('teams')

    # Drop ENUM types
    team_role = sa.Enum('owner', 'admin', 'member', 'viewer', name='teamrole')
    team_status = sa.Enum('active', 'inactive', 'archived', name='teamstatus')

    team_status.drop(bind, checkfirst=True)
    team_role.drop(bind, checkfirst=True)