"""change crop table

Revision ID: b1a695c9aaf0
Revises: 678a325552b7
Create Date: 2024-08-02 15:47:38.814577

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1a695c9aaf0'
down_revision: Union[str, None] = '678a325552b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('crops', 'temp_time_delta')
    op.drop_column('crops', 'moist_time_delta')
    op.add_column('crops', sa.Column('altitude', sa.String()))
    op.add_column('crops', sa.Column('variety', sa.String()))
    op.add_column('crops', sa.Column('clima', sa.String()))
    op.add_column('crops', sa.Column('distance', sa.String()))
    op.add_column('crops', sa.Column('density', sa.String()))
    op.add_column('crops', sa.Column('depth', sa.String()))
    op.add_column('crops', sa.Column('norm', sa.String()))
    op.add_column('crops', sa.Column('method', sa.String()))
    op.add_column('crops', sa.Column('min_temp', sa.String()))
    op.add_column('crops', sa.Column('fertilization', sa.String()))
    op.add_column('crops', sa.Column('watering', sa.String()))
    op.add_column('crops', sa.Column('care', sa.String()))
    op.add_column('crops', sa.Column('protection', sa.String()))
    op.add_column('crops', sa.Column('utilization', sa.String()))
    op.add_column('crops', sa.Column('harvest', sa.String()))
    op.add_column('crops', sa.Column('storage', sa.String()))
    op.add_column('crops', sa.Column('season_start', sa.DateTime(timezone=True)))
    op.add_column('crops', sa.Column('season_end', sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column('crops', 'altitude')
    op.drop_column('crops', 'variety')
    op.drop_column('crops', 'clima')
    op.drop_column('crops', 'distance')
    op.drop_column('crops', 'density')
    op.drop_column('crops', 'depth')
    op.drop_column('crops', 'norm')
    op.drop_column('crops', 'method')
    op.drop_column('crops', 'min_temp')
    op.drop_column('crops', 'fertilization')
    op.drop_column('crops', 'watering')
    op.drop_column('crops', 'care')
    op.drop_column('crops', 'protection')
    op.drop_column('crops', 'utilization')
    op.drop_column('crops', 'harvest')
    op.drop_column('crops', 'storage')
    op.drop_column('crops', 'season_start')
    op.drop_column('crops', 'season_end')
