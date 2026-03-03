"""add indexes for quotation timeout paths

Revision ID: 91af3b7e2d11
Revises: 6d2f8a1c9b4e
Create Date: 2026-03-03 00:00:00.000000
"""

from alembic import op


revision = '91af3b7e2d11'
down_revision = '6d2f8a1c9b4e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_quotation_company_status_valid_until', 'quotation', ['company_id', 'status', 'valid_until'], unique=False)
    op.create_index('ix_quotation_company_date', 'quotation', ['company_id', 'date'], unique=False)
    op.create_index('ix_order_company_quotation', 'order', ['company_id', 'quotation_id'], unique=False)


def downgrade():
    op.drop_index('ix_order_company_quotation', table_name='order')
    op.drop_index('ix_quotation_company_date', table_name='quotation')
    op.drop_index('ix_quotation_company_status_valid_until', table_name='quotation')
