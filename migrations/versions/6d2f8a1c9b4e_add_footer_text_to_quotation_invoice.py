"""add footer_text to quotation and invoice

Revision ID: 6d2f8a1c9b4e
Revises: 3c9b4f1d2a77
Create Date: 2026-03-03 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = '6d2f8a1c9b4e'
down_revision = '3c9b4f1d2a77'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('quotation', sa.Column('footer_text', sa.Text(), nullable=True))
    op.add_column('invoice', sa.Column('footer_text', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('invoice', 'footer_text')
    op.drop_column('quotation', 'footer_text')
