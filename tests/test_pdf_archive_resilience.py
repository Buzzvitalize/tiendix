import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import app as app_module
from app import app, db, _create_company_user_from_signup, _company_private_token, _company_short_slug
from models import CompanyInfo, User, Client, Product, Warehouse, ProductStock, Quotation


def test_new_quotation_does_not_fail_when_pdf_generation_breaks(tmp_path, monkeypatch):
    db_path = tmp_path / 'test.sqlite'
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['PDF_ARCHIVE_ROOT'] = str(tmp_path / 'pdf_archive')
    app.config['PUBLIC_DOCS_BASE_URL'] = 'https://app.ecosea.do'

    with app.app_context():
        db.session.remove()
        db.engine.dispose()
        db.drop_all()
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

    def _boom(*_args, **_kwargs):
        raise RuntimeError('forced failure')

    monkeypatch.setattr(app_module, '_build_quotation_pdf_bytes', _boom)

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
        }, follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/cotizaciones')
    with app.app_context():
        assert Quotation.query.count() == 1


def test_signup_company_dirs_created_and_personal_name_fallback(tmp_path):
    db_path = tmp_path / 'test.sqlite'
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['PDF_ARCHIVE_ROOT'] = str(tmp_path / 'pdf_archive')

    with app.app_context():
        db.session.remove()
        db.engine.dispose()
        db.drop_all()
        db.create_all()

        company, _user = _create_company_user_from_signup(
            first_name='Juan',
            last_name='Pérez',
            company_name='',
            identifier='',
            phone='8090000000',
            address='Santo Domingo',
            website=None,
            username='juanp',
            password_hash='x:y',
            email='juan@example.com',
            role='company',
        )
        db.session.commit()

        assert company.name == 'Juan Pérez'
        slug = _company_short_slug(company.name)
        token = _company_private_token(company.id, company.name)
        root = tmp_path / 'pdf_archive' / slug / token
        assert (root / 'cotizacion').exists()
        assert (root / 'pedido').exists()
        assert (root / 'factura').exists()
        assert (root / 'estado_cuenta').exists()
        assert (root / 'reporte').exists()
