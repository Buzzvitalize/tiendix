import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ai import recommend_products
from app import app, db
from models import CompanyInfo, OrderItem, User


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / 'test.sqlite'
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    with app.app_context():
        db.create_all()

        comp1 = CompanyInfo(name='Comp 1', street='', sector='', province='', phone='', rnc='')
        comp2 = CompanyInfo(name='Comp 2', street='', sector='', province='', phone='', rnc='')
        db.session.add_all([comp1, comp2])
        db.session.flush()

        u1 = User(username='user1', first_name='U', last_name='One', role='company', company_id=comp1.id)
        u1.set_password('pass')
        u2 = User(username='user2', first_name='U', last_name='Two', role='company', company_id=comp2.id)
        u2.set_password('pass')
        db.session.add_all([u1, u2])

        db.session.add_all(
            [
                OrderItem(
                    order_id=1,
                    code='A1',
                    reference='R1',
                    product_name='Producto A',
                    unit='Unidad',
                    unit_price=100,
                    quantity=5,
                    discount=0,
                    company_id=comp1.id,
                ),
                OrderItem(
                    order_id=2,
                    code='B1',
                    reference='R2',
                    product_name='Producto B',
                    unit='Unidad',
                    unit_price=50,
                    quantity=10,
                    discount=0,
                    company_id=comp2.id,
                ),
            ]
        )
        db.session.commit()

    with app.test_client() as client:
        yield client

    with app.app_context():
        db.drop_all()
    if db_path.exists():
        db_path.unlink()


def login(client, username):
    return client.post('/login', data={'username': username, 'password': 'pass'}, follow_redirects=True)


def test_recommendations_are_isolated_per_company(client):
    login(client, 'user1')
    resp = client.get('/api/recommendations')

    assert resp.status_code == 200
    assert resp.get_json() == {'products': ['Producto A']}


def test_recommend_products_returns_empty_when_company_is_none(client):
    with app.app_context():
        assert recommend_products(None) == []
