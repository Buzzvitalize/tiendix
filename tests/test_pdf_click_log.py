import os
import sys
from datetime import timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import app as app_module
from app import app, db
from models import CompanyInfo, User, Client, Quotation, QuotationItem


def test_quotation_pdf_click_writes_ok_log(tmp_path):
    db_path = tmp_path / 'test.sqlite'
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['PDF_ARCHIVE_ROOT'] = str(tmp_path / 'pdf_archive')
    app.config['PDF_LOG_DIR'] = str(tmp_path / 'logpdf')

    with app.app_context():
        db.session.remove()
        db.engine.dispose()
        db.drop_all()
        db.create_all()

        company = CompanyInfo(name='CompA', street='', sector='', province='', phone='', rnc='')
        db.session.add(company)
        db.session.flush()

        user = User(username='u_pdf_log', first_name='User', last_name='Log', role='company', company_id=company.id)
        user.set_password('pass')
        db.session.add(user)

        client = Client(name='Alice', company_id=company.id)
        db.session.add(client)
        db.session.flush()

        q = Quotation(client_id=client.id, subtotal=100, itbis=18, total=118, seller='User Log', payment_method='Efectivo', company_id=company.id, valid_until=app_module.dom_now() + timedelta(days=30))
        db.session.add(q)
        db.session.flush()
        db.session.add(QuotationItem(quotation_id=q.id, code='P1', product_name='Prod', unit='Unidad', unit_price=100, quantity=1, company_id=company.id))
        db.session.commit()

    with app.test_client() as client:
        client.post('/login', data={'username': 'u_pdf_log', 'password': 'pass'})
        resp = client.get('/cotizaciones/1/pdf')

    assert resp.status_code == 200
    log_file = tmp_path / 'logpdf' / 'cotizacion.log'
    assert log_file.exists()
    content = log_file.read_text(encoding='utf-8')
    assert '|ok|' in content
