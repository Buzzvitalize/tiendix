"""add valid_until to quotation

Revision ID: 1b60f7130a5a
Revises: 4b3f24c55f2b
Create Date: 2025-02-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1b60f7130a5a'
down_revision = '4b3f24c55f2b'
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {col['name'] for col in inspector.get_columns(table_name)}


def upgrade():
    if not _has_column('quotation', 'valid_until'):
        op.add_column('quotation', sa.Column('valid_until', sa.DateTime(), nullable=True))
    op.execute("UPDATE quotation SET valid_until = datetime(date, '+30 day') WHERE valid_until IS NULL")
    if op.get_bind().dialect.name != 'sqlite':
        op.alter_column('quotation', 'valid_until', nullable=False)


def downgrade():
    if _has_column('quotation', 'valid_until'):
        op.drop_column('quotation', 'valid_until')
