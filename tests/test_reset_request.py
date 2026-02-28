import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import app, db
from models import User, CompanyInfo


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / 'test.sqlite'
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    with app.app_context():
        db.drop_all()
        db.create_all()
        company = CompanyInfo(name='C', street='', sector='', province='', phone='', rnc='')
        db.session.add(company)
        db.session.flush()
        user = User(username='u', email='u@example.com', first_name='F', last_name='L', role='company', company_id=company.id)
        user.set_password('pw')
        db.session.add(user)
        db.session.commit()
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.drop_all()
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def csrf_client(tmp_path):
    db_path = tmp_path / 'test.sqlite'
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['WTF_CSRF_ENABLED'] = True
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.drop_all()
    app.config['WTF_CSRF_ENABLED'] = False
    if db_path.exists():
        db_path.unlink()


def test_reset_request_redirects(client):
    resp = client.post('/reset', data={'email': 'u@example.com'})
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/login')


def test_reset_request_requires_csrf(csrf_client):
    resp = csrf_client.post('/reset', data={'email': 'x@example.com'})
    assert resp.status_code == 400


def test_reset_request_page_accessible(client):
    resp = client.get('/reset')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'Recuperar contraseña' in body
    assert 'Regresar al login' in body


def test_reset_request_sends_recovery_email_sync(client, monkeypatch):
    sent = {}

    def fake_send_email(to, subject, html, attachments=None, asynchronous=True):
        sent['to'] = to
        sent['subject'] = subject
        sent['html'] = html
        sent['async'] = asynchronous

    monkeypatch.setattr('app.send_email', fake_send_email)

    resp = client.post('/reset', data={'email': 'u@example.com'})
    assert resp.status_code == 302
    assert sent['to'] == 'u@example.com'
    assert sent['subject'] == '[Tiendix] - recuperacion de contraseña'
    assert '/recovery/' in sent['html']
    assert sent['async'] is False


def test_recovery_alias_route_is_accessible(client):
    with app.app_context():
        user = User.query.filter_by(email='u@example.com').first()
        from auth import generate_reset_token
        token = generate_reset_token(user)
    resp = client.get(f'/recovery/{token}')
    assert resp.status_code == 200
