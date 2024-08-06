"""add phone

Revision ID: 5fec4e604b25
Revises: 53cfbc1e5ae4
Create Date: 2024-07-11 13:07:31.187120

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5fec4e604b25'
down_revision: Union[str, None] = '53cfbc1e5ae4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('phone', sa.BigInteger()))


def downgrade() -> None:
    op.drop_column('users', 'phone')
