import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app, db
from models import CompanyInfo, User, Client


def test_account_statement_detail_displays_full_name_and_link(tmp_path):
    db_path = tmp_path / "test.sqlite"
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['PUBLIC_DOCS_BASE_URL'] = 'https://app.ecosea.do'

    with app.app_context():
        db.drop_all()
        db.create_all()
        company = CompanyInfo(name='Eco Sea SRL', street='', sector='', province='', phone='', rnc='')
        db.session.add(company)
        db.session.flush()
        user = User(username='u_stmt', first_name='A', last_name='B', role='company', company_id=company.id)
        user.set_password('pass')
        db.session.add(user)
        client = Client(name='Juan', last_name='Perez', company_id=company.id)
        db.session.add(client)
        db.session.commit()

    with app.test_client() as c:
        c.post('/login', data={'username': 'u_stmt', 'password': 'pass'})
        resp = c.get('/reportes/estado-cuentas/1')

    body = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert 'Juan Perez' in body
    assert '/generated_docs/' in body
    assert 'target="_blank"' in body


def test_account_statement_pdf_bytes_legacy_cell_signature(monkeypatch):
    import account_pdf

    monkeypatch.setattr(account_pdf, '_CELL_SUPPORTS_NEW_X', False)
    data = account_pdf.generate_account_statement_pdf_bytes(
        {'name': 'Compania', 'street': '', 'phone': '', 'rnc': '', 'logo': None},
        {'name': 'Cliente Test', 'identifier': '', 'street': '', 'sector': '', 'province': '', 'phone': '', 'email': ''},
        [{'document': 'Factura 1', 'order': 1, 'date': '01/03/2026', 'due': '15/03/2026', 'info': 'Pendiente', 'amount': 100, 'balance': 100}],
        100,
        {'0-30': 100, '31-60': 0, '61-90': 0, '91-120': 0, '121+': 0},
        100.0,
    )
    assert data.startswith(b'%PDF')
