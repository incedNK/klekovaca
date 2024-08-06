"""added status to sensor data

Revision ID: 678a325552b7
Revises: 5fec4e604b25
Create Date: 2024-07-15 15:52:25.234441

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '678a325552b7'
down_revision: Union[str, None] = '5fec4e604b25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sensor_data', sa.Column('status', sa.Integer()))


def downgrade() -> None:
    op.drop_column('sensor_data', 'status')
