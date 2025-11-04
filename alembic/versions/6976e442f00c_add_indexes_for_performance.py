"""add indexes for performance

Revision ID: 6976e442f00c
Revises: 2fe7bd3a35d8
Create Date: 2025-11-04 09:13:49.575048

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6976e442f00c'
down_revision: Union[str, Sequence[str], None] = '2fe7bd3a35d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 인덱스 생성
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_photos_user_id', 'photos', ['user_id'])
    op.create_index('idx_photos_created_at', 'photos', ['uploaded_at'])
    op.create_index('idx_worldcups_user_id', 'worldcups', ['user_id'])
    op.create_index('idx_worldcups_created_at', 'worldcups', ['created_at'])
    op.create_index('idx_worldcups_status', 'worldcups', ['status'])
    op.create_index('idx_matches_worldcup_id', 'matches', ['worldcup_id'])
    op.create_index('idx_shares_worldcup_id', 'shares', ['worldcup_id'])


def downgrade() -> None:
    # 인덱스 삭제 (역순)
    op.drop_index('idx_shares_worldcup_id')
    op.drop_index('idx_matches_worldcup_id')
    op.drop_index('idx_worldcups_status')
    op.drop_index('idx_worldcups_created_at')
    op.drop_index('idx_worldcups_user_id')
    op.drop_index('idx_photos_created_at')
    op.drop_index('idx_photos_user_id')
    op.drop_index('idx_users_email')
