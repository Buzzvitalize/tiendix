"""add terms acceptance to account_request

Revision ID: 7f4677f2443e
Revises: 53842ef09674
Create Date: 2025-08-29 14:10:55.638310
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7f4677f2443e'
down_revision = '53842ef09674'
branch_labels = None
depends_on = None


def _existing_columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {col['name'] for col in inspector.get_columns(table_name)}


def upgrade():
    columns = _existing_columns('account_request')

    if 'accepted_terms' not in columns:
        op.add_column(
            'account_request',
            sa.Column('accepted_terms', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        )
    if 'accepted_terms_at' not in columns:
        op.add_column('account_request', sa.Column('accepted_terms_at', sa.DateTime(), nullable=True))
    if 'accepted_terms_ip' not in columns:
        op.add_column('account_request', sa.Column('accepted_terms_ip', sa.String(length=45), nullable=True))
    if 'accepted_terms_user_agent' not in columns:
        op.add_column('account_request', sa.Column('accepted_terms_user_agent', sa.String(length=255), nullable=True))

    op.execute("UPDATE account_request SET accepted_terms=0 WHERE accepted_terms IS NULL")
    if op.get_bind().dialect.name != 'sqlite':
        op.alter_column('account_request', 'accepted_terms', server_default=None)


def downgrade():
    columns = _existing_columns('account_request')
    if 'accepted_terms_user_agent' in columns:
        op.drop_column('account_request', 'accepted_terms_user_agent')
    if 'accepted_terms_ip' in columns:
        op.drop_column('account_request', 'accepted_terms_ip')
    if 'accepted_terms_at' in columns:
        op.drop_column('account_request', 'accepted_terms_at')
    if 'accepted_terms' in columns:
        op.drop_column('account_request', 'accepted_terms')
