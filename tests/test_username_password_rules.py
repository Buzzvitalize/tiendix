import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import app, db
from models import User, AccountRequest, CompanyInfo


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
        u = User(username='existing', first_name='A', last_name='B', role='company', company_id=company.id)
        u.set_password('123456')
        db.session.add(u)
        db.session.commit()
    with app.test_client() as c:
        yield c
    with app.app_context():
        db.drop_all()
    if db_path.exists():
        db_path.unlink()


def _base_payload(**kwargs):
    payload = {
        'account_type': 'personal',
        'first_name': 'Juan',
        'last_name': 'Perez',
        'company': 'Mi Empresa',
        'identifier': '12345678901',
        'phone': '8091234567',
        'email': 'jp@example.com',
        'username': 'NuevoUser',
        'password': '123456',
        'confirm_password': '123456',
        'accepted_terms': 'y',
    }
    payload.update(kwargs)
    return payload


def test_request_account_username_saved_lowercase(client):
    client.post('/solicitar-cuenta', data=_base_payload(), follow_redirects=True)
    with app.app_context():
        req = AccountRequest.query.first()
        assert req is not None
        assert req.username == 'nuevouser'


def test_request_account_rejects_short_password(client):
    resp = client.post('/solicitar-cuenta', data=_base_payload(password='12345', confirm_password='12345'), follow_redirects=True)
    assert b'minimo 6' in resp.data.lower() or b'm\xc3\xadnimo 6' in resp.data.lower()


def test_request_account_rejects_case_insensitive_duplicate_username(client):
    resp = client.post('/solicitar-cuenta', data=_base_payload(username='ExIsTiNg'), follow_redirects=True)
    assert b'ya existe' in resp.data.lower()
