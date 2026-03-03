"""add report indexes

Revision ID: 3c9b4f1d2a77
Revises: 8e1f9d2c4b7a
Create Date: 2026-03-03 00:00:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '3c9b4f1d2a77'
down_revision = '8e1f9d2c4b7a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_invoice_company_date', 'invoice', ['company_id', 'date'], unique=False)
    op.create_index('ix_invoice_company_status_date', 'invoice', ['company_id', 'status', 'date'], unique=False)
    op.create_index('ix_invoice_item_company_category', 'invoice_item', ['company_id', 'category'], unique=False)
    op.create_index('ix_invoice_item_invoice_company', 'invoice_item', ['invoice_id', 'company_id'], unique=False)


def downgrade():
    op.drop_index('ix_invoice_item_invoice_company', table_name='invoice_item')
    op.drop_index('ix_invoice_item_company_category', table_name='invoice_item')
    op.drop_index('ix_invoice_company_status_date', table_name='invoice')
    op.drop_index('ix_invoice_company_date', table_name='invoice')
