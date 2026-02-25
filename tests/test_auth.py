import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import app, db
from models import User


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test.sqlite"
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    with app.app_context():
        db.create_all()
        u = User(username='admin', first_name='Ad', last_name='Min', role='admin')
        u.set_password('363636')
        db.session.add(u)
        db.session.commit()
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.drop_all()
    if db_path.exists():
        db_path.unlink()


def test_login(client):
    resp = client.post('/login', data={'username': 'admin', 'password': '363636'})
    assert resp.status_code == 302



def test_password_is_hashed(client):
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        assert user.password != '363636'
        assert ':' in user.password


def test_sidebar_hides_contabilidad_menu(client):
    client.post('/login', data={'username': 'admin', 'password': '363636'})
    resp = client.get('/', follow_redirects=True)
    assert b'Contabilidad' not in resp.data



def test_dom_time_visible_after_login(client):
    client.post('/login', data={'username': 'admin', 'password': '363636'})
    resp = client.get('/', follow_redirects=True)
    assert b'Hora RD:' in resp.data
