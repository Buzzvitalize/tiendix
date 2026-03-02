from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd0fe5fa26c0e'
down_revision = '9a12859f36b3'
branch_labels = None
depends_on = None


def _has_unique(table_name: str, constraint_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return constraint_name in {c['name'] for c in inspector.get_unique_constraints(table_name) if c.get('name')}


def upgrade():
    if op.get_bind().dialect.name == 'sqlite':
        return
    if not _has_unique('client', 'uq_client_identifier_company'):
        op.create_unique_constraint('uq_client_identifier_company', 'client', ['identifier', 'company_id'])
    if not _has_unique('client', 'uq_client_email_company'):
        op.create_unique_constraint('uq_client_email_company', 'client', ['email', 'company_id'])


def downgrade():
    if op.get_bind().dialect.name == 'sqlite':
        return
    if _has_unique('client', 'uq_client_email_company'):
        op.drop_constraint('uq_client_email_company', 'client', type_='unique')
    if _has_unique('client', 'uq_client_identifier_company'):
        op.drop_constraint('uq_client_identifier_company', 'client', type_='unique')
