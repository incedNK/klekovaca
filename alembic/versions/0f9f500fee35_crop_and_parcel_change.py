"""crop and parcel change

Revision ID: 0f9f500fee35
Revises: b1a695c9aaf0
Create Date: 2024-08-06 13:06:47.445615

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f9f500fee35'
down_revision: Union[str, None] = 'b1a695c9aaf0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('crops', sa.Column('crop_yield', sa.String()))
    op.add_column('crops', sa.Column('rain', sa.Float()))
    op.add_column('parcels', sa.Column('sow_complete', sa.Boolean()))


def downgrade() -> None:
    op.drop_column('crops', 'crop_yield')
    op.drop_column('crops', 'rain')
    op.drop_column('parcels', 'sow_complete')
