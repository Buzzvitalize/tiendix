"""add executed_by to inventory movement"""
from alembic import op
import sqlalchemy as sa

revision = '9a12859f36b3'
down_revision = '7f4677f2443e'
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column_name in {col['name'] for col in inspector.get_columns(table_name)}


def _has_fk(table_name: str, constrained_columns: list[str], referred_table: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    for fk in inspector.get_foreign_keys(table_name):
        if fk.get('referred_table') == referred_table and fk.get('constrained_columns') == constrained_columns:
            return True
    return False


def upgrade():
    if not _has_column('inventory_movement', 'executed_by'):
        op.add_column('inventory_movement', sa.Column('executed_by', sa.Integer(), nullable=True))
    if not _has_fk('inventory_movement', ['executed_by'], 'user'):
        op.create_foreign_key('fk_inventory_movement_executed_by_user', 'inventory_movement', 'user', ['executed_by'], ['id'])


def downgrade():
    if _has_fk('inventory_movement', ['executed_by'], 'user'):
        op.drop_constraint('fk_inventory_movement_executed_by_user', 'inventory_movement', type_='foreignkey')
    if _has_column('inventory_movement', 'executed_by'):
        op.drop_column('inventory_movement', 'executed_by')
