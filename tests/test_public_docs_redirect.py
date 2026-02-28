import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app, db
from models import CompanyInfo, User, Client, Product, Warehouse, ProductStock


def test_first_quotation_redirects_to_public_docs_url(tmp_path):
    db_path = tmp_path / 'test.sqlite'
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['PUBLIC_DOCS_BASE_URL'] = 'https://app.ecosea.do'

    with app.app_context():
        db.session.remove()
        db.engine.dispose()
        db.create_all()

        company = CompanyInfo(name='Eco Sea SRL', street='', sector='', province='', phone='', rnc='')
        db.session.add(company)
        db.session.flush()

        user = User(username='user1', first_name='User', last_name='One', role='company', company_id=company.id)
        user.set_password('pass')
        db.session.add(user)

        client = Client(name='Alice', company_id=company.id)
        db.session.add(client)

        product = Product(code='P1', name='Prod', unit='Unidad', price=100, stock=10, min_stock=2, company_id=company.id)
        db.session.add(product)

        warehouse = Warehouse(name='W1', company_id=company.id)
        db.session.add(warehouse)
        db.session.flush()

        stock = ProductStock(product_id=product.id, warehouse_id=warehouse.id, stock=10, min_stock=2, company_id=company.id)
        db.session.add(stock)
        db.session.commit()

    with app.test_client() as client:
        client.post('/login', data={'username': 'user1', 'password': 'pass'})
        resp = client.post('/cotizaciones/nueva', data={
            'client_id': '1',
            'seller': 'User One',
            'payment_method': 'Efectivo',
            'warehouse_id': '1',
            'product_id[]': ['1'],
            'product_quantity[]': ['1'],
            'product_discount[]': ['0'],
        })

    assert resp.status_code == 302
    assert resp.headers['Location'].startswith('https://app.ecosea.do/eco-sea-srl/')
    assert '/cotizacion/01.pdf' in resp.headers['Location']
    token = resp.headers['Location'].split('/')[4]
    assert len(token) == 6
    assert token.isdigit()

    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
