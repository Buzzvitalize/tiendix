import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import app as app_module
from app import app, db, _archive_pdf_copy
from models import CompanyInfo, User, Client, Quotation


def test_quotation_pdf_uses_archived_copy_when_generation_fails(tmp_path, monkeypatch):
    db_path = tmp_path / 'test.sqlite'
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['PDF_ARCHIVE_ROOT'] = str(tmp_path / 'pdf_archive')

    with app.app_context():
        db.session.remove()
        db.engine.dispose()
        db.drop_all()
        db.create_all()
        company = CompanyInfo(name='Eco Sea SRL', street='', sector='', province='', phone='', rnc='')
        db.session.add(company)
        db.session.flush()
        user = User(username='fallback_user', first_name='User', last_name='One', role='company', company_id=company.id)
        user.set_password('pass')
        db.session.add(user)
        client = Client(name='Alice', company_id=company.id)
        db.session.add(client)
        db.session.flush()
        now = datetime.utcnow()
        q = Quotation(
            client_id=client.id,
            subtotal=100,
            itbis=18,
            total=118,
            seller='User One',
            payment_method='Efectivo',
            company_id=company.id,
            date=now,
            valid_until=now + timedelta(days=30),
        )
        db.session.add(q)
        db.session.commit()
        company_id = company.id
        quotation_id = q.id

    with app.test_request_context('/'):
        from flask import session
        session['company_id'] = company_id
        _archive_pdf_copy('cotizacion', quotation_id, b'%PDF-1.4 archived-copy', company_id=company_id, company_name='Eco Sea SRL')

    def _boom(*_args, **_kwargs):
        raise RuntimeError('forced failure')

    monkeypatch.setattr(app_module, '_build_quotation_pdf_bytes', _boom)

    with app.test_client() as client:
        client.post('/login', data={'username': 'fallback_user', 'password': 'pass'})
        with client.session_transaction() as sess:
            sess['company_id'] = company_id
        resp = client.get(f'/cotizaciones/{quotation_id}/pdf')

    assert resp.status_code == 200
    assert resp.headers['Content-Type'].startswith('application/pdf')

    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
