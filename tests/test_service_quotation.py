import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app, db
from models import CompanyInfo, User, Client


def _seed_base(tmp_path):
    db_path = tmp_path / 'test.sqlite'
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    with app.app_context():
        db.drop_all()
        db.create_all()
        company = CompanyInfo(name='Carlos SRL', street='', sector='', province='', phone='', rnc='')
        db.session.add(company)
        db.session.flush()
        user = User(username='svcuser', first_name='Carlos', last_name='Tester', role='company', company_id=company.id)
        user.set_password('pass')
        db.session.add(user)
        client = Client(name='Cliente Servicio', company_id=company.id, email='cliente@example.com')
        db.session.add(client)
        db.session.commit()


def test_cotizaciones_page_shows_nuevo_servicio_button(tmp_path):
    _seed_base(tmp_path)
    with app.test_client() as c:
        c.post('/login', data={'username': 'svcuser', 'password': 'pass'})
        html = c.get('/cotizaciones').get_data(as_text=True)
    assert 'Nuevo Servicio' in html
    assert '/cotizaciones/nuevo-servicio' in html


def test_create_service_quotation_without_warehouse_archives_in_servicios(tmp_path, monkeypatch):
    _seed_base(tmp_path)
    captured = {}

    def _fake_archive(doc_type, doc_number, pdf_data, company_name=None, company_id=None):
        captured['doc_type'] = doc_type
        captured['doc_number'] = doc_number
        return None

    monkeypatch.setattr('app._archive_pdf_copy', _fake_archive)

    with app.test_client() as c:
        c.post('/login', data={'username': 'svcuser', 'password': 'pass'})
        resp = c.post('/cotizaciones/nuevo-servicio', data={
            'client_id': '1',
            'seller': 'Carlos Tester',
            'payment_method': 'Efectivo',
            'validity_period': '1m',
            'service_name[]': ['Biorat'],
            'service_description[]': ['funciona para ratones'],
            'service_quantity[]': ['2'],
            'service_rate[]': ['1500'],
            'note': 'Servicio especial',
        }, follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/cotizaciones')
    assert captured['doc_type'] == 'servicios'

    with app.app_context():
        from models import Quotation
        q = Quotation.query.first()
        assert q is not None
        assert q.warehouse_id is None
