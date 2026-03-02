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


def test_account_statement_link_only_fallbacks_to_direct_pdf_when_archive_fails(tmp_path, monkeypatch):
    db_path = tmp_path / "test.sqlite"
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    with app.app_context():
        db.drop_all()
        db.create_all()
        company = CompanyInfo(name='Eco Sea SRL', street='', sector='', province='', phone='', rnc='')
        db.session.add(company)
        db.session.flush()
        user = User(username='u_stmt_fallback', first_name='A', last_name='B', role='company', company_id=company.id)
        user.set_password('pass')
        db.session.add(user)
        client = Client(name='Juan', last_name='Perez', company_id=company.id)
        db.session.add(client)
        db.session.commit()

    monkeypatch.setattr('app._archive_pdf_copy', lambda *args, **kwargs: None)

    with app.test_client() as c:
        c.post('/login', data={'username': 'u_stmt_fallback', 'password': 'pass'})
        resp = c.get('/reportes/estado-cuentas/1?pdf=1&link_only=1')

    assert resp.status_code == 200
    data = resp.get_json()
    assert data['ok'] is True
    assert data['archived'] is False
    assert data['url'].endswith('/reportes/estado-cuentas/1?pdf=1')
def test_account_statement_pdf_bytes_handles_string_output(monkeypatch):
    import account_pdf
    original_output = account_pdf.FPDF.output
    def fake_output(self, *args, **kwargs):
        return '%PDF-1.4\n%stub'
    monkeypatch.setattr(account_pdf.FPDF, 'output', fake_output)
    try:
        data = account_pdf.generate_account_statement_pdf_bytes(
            {'name': 'Compania', 'street': '', 'phone': '', 'rnc': '', 'logo': None},
            {'name': 'Cliente Test', 'identifier': '', 'street': '', 'sector': '', 'province': '', 'phone': '', 'email': ''},
            [],
            0,
            {'0-30': 0, '31-60': 0, '61-90': 0, '91-120': 0, '121+': 0},
            0.0,
        )
        assert isinstance(data, bytes)
        assert data.startswith(b'%PDF')
    finally:
        monkeypatch.setattr(account_pdf.FPDF, 'output', original_output)
