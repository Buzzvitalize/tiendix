import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app, db, _company_pdf_path, _company_pdf_dir
from models import CompanyInfo, User


def _login_as_company(client, company_id):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'company'
        sess['company_id'] = company_id


def test_company_pdf_path_uses_slug_token_and_doc_type(tmp_path):
    db_path = tmp_path / 'test.sqlite'
    static_root = tmp_path / 'static'
    app.static_folder = str(static_root)
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    with app.app_context():
        db.drop_all()
        db.create_all()
        c = CompanyInfo(name='Eco Sea SRL', street='', sector='', province='', phone='', rnc='')
        db.session.add(c)
        db.session.flush()
        db.session.add(User(username='u1', first_name='U', last_name='One', role='company', company_id=c.id, password='x:y'))
        db.session.commit()

    with app.test_request_context('/'):
        from flask import session
        session['company_id'] = 1
        first_path = _company_pdf_path('cotizaciones', 'cotizacion_1.pdf')
        second_path = _company_pdf_path('cotizaciones', 'cotizacion_2.pdf')

    rel_first = os.path.relpath(first_path, app.static_folder)
    parts = rel_first.split(os.sep)
    assert parts[0] == 'pdfs'
    assert parts[1] == 'eco-sea-srl'
    assert len(parts[2]) == 6
    assert parts[3] == 'cotizaciones'
    assert parts[4] == 'cotizacion_1.pdf'
    assert os.path.dirname(first_path) == os.path.dirname(second_path)

    with app.app_context():
        db.drop_all()


def test_pdf_route_isolated_to_current_company_folder(tmp_path):
    db_path = tmp_path / 'test.sqlite'
    static_root = tmp_path / 'static'
    app.static_folder = str(static_root)
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    with app.app_context():
        db.drop_all()
        db.create_all()
        c1 = CompanyInfo(name='Eco Sea', street='', sector='', province='', phone='', rnc='')
        c2 = CompanyInfo(name='Otra Co', street='', sector='', province='', phone='', rnc='')
        db.session.add_all([c1, c2])
        db.session.flush()
        db.session.add(User(username='u1', first_name='U', last_name='One', role='company', company_id=c1.id, password='x:y'))
        db.session.commit()

    with app.test_request_context('/'):
        from flask import session
        session['company_id'] = 1
        own_pdf = _company_pdf_path('pedidos', 'pedido_1.pdf')
        own_root = _company_pdf_dir().parent
    with app.test_request_context('/'):
        from flask import session
        session['company_id'] = 2
        other_pdf = _company_pdf_path('pedidos', 'pedido_2.pdf')

    os.makedirs(os.path.dirname(own_pdf), exist_ok=True)
    with open(own_pdf, 'wb') as f:
        f.write(b'%PDF-1.4 own')

    os.makedirs(os.path.dirname(other_pdf), exist_ok=True)
    with open(other_pdf, 'wb') as f:
        f.write(b'%PDF-1.4 other')

    rel_other = os.path.relpath(other_pdf, own_root)

    with app.test_client() as client:
        _login_as_company(client, 1)
        ok = client.get('/pdfs/pedidos/pedido_1.pdf')
        assert ok.status_code == 200

        blocked = client.get(f'/pdfs/{rel_other}')
        assert blocked.status_code == 404

    with app.app_context():
        db.drop_all()
