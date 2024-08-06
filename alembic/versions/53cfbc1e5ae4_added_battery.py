"""Added battery

Revision ID: 53cfbc1e5ae4
Revises: d9cc8f42156e
Create Date: 2024-07-09 16:12:39.815539

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53cfbc1e5ae4'
down_revision: Union[str, None] = 'd9cc8f42156e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('alerts', 'crop_id')
    op.add_column('sensor_data', sa.Column('battery', sa.Float()))


def downgrade() -> None:
    op.drop_column('sensor_data', 'battery')
