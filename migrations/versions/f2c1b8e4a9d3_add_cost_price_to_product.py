"""add cost price to product

Revision ID: f2c1b8e4a9d3
Revises: 1b60f7130a5a
Create Date: 2026-02-11
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2c1b8e4a9d3'
down_revision = '1b60f7130a5a'
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {col['name'] for col in inspector.get_columns(table_name)}


def upgrade():
    if not _has_column('product', 'cost_price'):
        op.add_column('product', sa.Column('cost_price', sa.Float(), nullable=True))


def downgrade():
    if _has_column('product', 'cost_price'):
        op.drop_column('product', 'cost_price')
