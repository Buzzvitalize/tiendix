import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import app, db
from models import User, CompanyInfo, ErrorReport


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / 'test.sqlite'
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    with app.app_context():
        db.create_all()
        company = CompanyInfo(name='Comp', street='', sector='', province='', phone='', rnc='')
        db.session.add(company)
        db.session.flush()
        admin = User(username='admin', first_name='Ad', last_name='Min', role='admin', company_id=company.id)
        admin.set_password('363636')
        user = User(username='user', first_name='U', last_name='Ser', role='company', company_id=company.id)
        user.set_password('123')
        db.session.add_all([admin, user])
        db.session.commit()
    with app.test_client() as c:
        yield c
    with app.app_context():
        db.drop_all()
    if db_path.exists():
        db_path.unlink()


def login(c, username='user', password='123'):
    return c.post('/login', data={'username': username, 'password': password})


def test_report_error_form_submit(client):
    login(client)
    resp = client.post('/reportar-problema', data={
        'title': 'Error al generar PDF',
        'module': 'PDF / Descargas',
        'severity': 'alta',
        'actual_behavior': 'Sale Internal Server Error',
        'steps_to_reproduce': '1. Ir a facturas 2. Clic PDF',
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'72 horas laborables' in resp.data
    with app.app_context():
        row = ErrorReport.query.first()
        assert row is not None
        assert row.severity == 'alta'


def test_report_error_requires_login(client):
    resp = client.get('/reportar-problema', follow_redirects=True)
    assert resp.status_code == 200
    assert b'login' in resp.data.lower()


def test_admin_can_view_error_reports(client):
    login(client)
    client.post('/reportar-problema', data={
        'title': 'Error login',
        'module': 'Login / Acceso',
        'severity': 'media',
        'actual_behavior': 'No deja entrar',
        'steps_to_reproduce': 'Intentar entrar',
    })
    client.get('/logout')
    login(client, 'admin', '363636')
    resp = client.get('/cpaneltx/reportes-error')
    assert resp.status_code == 200
    assert b'Reportes de errores' in resp.data
