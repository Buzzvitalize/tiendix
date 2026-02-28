import os
import sys
import pytest
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import app, db
from models import (
    CompanyInfo,
    User,
    Client,
    Product,
    Quotation,
    QuotationItem,
    Order,
    Invoice,
    InventoryMovement,
    Warehouse,
    ProductStock,
)


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test.sqlite"
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['PDF_ARCHIVE_ROOT'] = str(tmp_path / 'pdf_archive')
    app.config['PUBLIC_DOCS_BASE_URL'] = None
    with app.app_context():
        db.session.remove()
        db.engine.dispose()
        db.create_all()
        c1 = CompanyInfo(name='CompA', street='', sector='', province='', phone='', rnc='')
        c2 = CompanyInfo(name='CompB', street='', sector='', province='', phone='', rnc='')
        db.session.add_all([c1, c2])
        db.session.flush()
        u1 = User(username='user1', first_name='User', last_name='One', role='company', company_id=c1.id)
        u1.set_password('pass')
        u2 = User(username='user2', first_name='User', last_name='Two', role='company', company_id=c2.id)
        u2.set_password('pass')
        admin = User(username='admin', first_name='Ad', last_name='Min', role='admin')
        admin.set_password('363636')
        db.session.add_all([u1, u2, admin])
        cl1 = Client(name='Alice', company_id=c1.id)
        cl2 = Client(name='BobCorp', is_final_consumer=False, company_id=c2.id)
        db.session.add_all([cl1, cl2])
        db.session.flush()
        prod = Product(code='P1', name='Prod', unit='Unidad', price=100, stock=10, min_stock=2, company_id=c1.id)
        db.session.add(prod)
        w = Warehouse(name='W1', company_id=c1.id)
        db.session.add(w)
        db.session.flush()
        ps = ProductStock(product_id=prod.id, warehouse_id=w.id, stock=10, min_stock=2, company_id=c1.id)
        db.session.add(ps)
        now = datetime.utcnow()
        q = Quotation(
            client_id=cl1.id,
            subtotal=100,
            itbis=18,
            total=118,
            seller='User One',
            payment_method='Efectivo',
            warehouse_id=w.id,
            company_id=c1.id,
            date=now,
            valid_until=now + timedelta(days=30),
        )
        db.session.add(q)
        db.session.flush()
        qi = QuotationItem(
            quotation_id=q.id,
            code='P1',
            product_name='Prod',
            unit='Unidad',
            unit_price=100,
            quantity=1,
            company_id=c1.id,
        )
        db.session.add(qi)
        db.session.commit()
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
    if db_path.exists():
        db_path.unlink()


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password})


def test_multi_tenant_isolation(client):
    login(client, 'user1', 'pass')
    resp = client.get('/clientes')
    assert b'Alice' in resp.data
    assert b'BobCorp' not in resp.data
    client.get('/logout')
    login(client, 'user2', 'pass')
    resp = client.get('/clientes')
    assert b'BobCorp' in resp.data
    assert b'Alice' not in resp.data


def test_conversion_and_pdf(client):
    login(client, 'user1', 'pass')
    quote_pdf = client.get('/cotizaciones/1/pdf')
    assert quote_pdf.status_code == 200
    client.post('/cotizaciones/1/convertir')
    with app.app_context():
        order = Order.query.first()
        order_id = order.id
    client.get(f'/pedidos/{order_id}/facturar')
    with app.app_context():
        invoice = Invoice.query.filter_by(order_id=order_id).order_by(Invoice.id.desc()).first()
        assert invoice is not None
        product = Product.query.filter_by(code='P1').first()
        movement = InventoryMovement.query.filter_by(product_id=product.id, reference_type='Order', reference_id=order_id).first()
    assert product.stock == 9
    assert movement is not None
    resp = client.get(f'/facturas/{invoice.id}/pdf')
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'application/pdf'


def test_unique_ncf_generation(client):
    login(client, 'user1', 'pass')
    # first conversion
    client.post('/cotizaciones/1/convertir')
    with app.app_context():
        order1 = Order.query.first()
    client.get(f'/pedidos/{order1.id}/facturar')
    # second conversion of same quotation creates new order
    client.post('/cotizaciones/1/convertir')
    with app.app_context():
        order2 = Order.query.order_by(Order.id.desc()).first()
    client.get(f'/pedidos/{order2.id}/facturar')
    with app.app_context():
        ncfs = [inv.ncf for inv in Invoice.query.order_by(Invoice.id).all()]
    assert len(ncfs) == 2
    assert ncfs[0] != ncfs[1]


def test_role_validation(client):
    login(client, 'user1', 'pass')
    resp = client.get('/admin/companies')
    assert resp.status_code == 302
    client.get('/logout')
    login(client, 'admin', '363636')
    resp = client.get('/admin/companies')
    assert resp.status_code == 200


def test_new_quotation_with_warehouse(client):
    login(client, 'user1', 'pass')
    client.post('/cotizaciones/nueva', data={
        'client_id': '1',
        'seller': 'User One',
        'payment_method': 'Efectivo',
        'warehouse_id': '1',
        'product_id[]': ['1'],
        'product_quantity[]': ['2'],
        'product_discount[]': ['0'],
    })
    with app.app_context():
        q = Quotation.query.order_by(Quotation.id.desc()).first()
        assert q.warehouse_id == 1
    client.post(f'/cotizaciones/{q.id}/convertir')
    with app.app_context():
        ps = ProductStock.query.filter_by(product_id=1, warehouse_id=1).first()
        assert ps.stock == 8



def test_new_quotation_creates_archive_file(client):
    login(client, 'user1', 'pass')
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
    with app.app_context():
        q = Quotation.query.order_by(Quotation.id.desc()).first()
    archive_root = Path(app.config['PDF_ARCHIVE_ROOT'])
    assert list(archive_root.glob(f'compa/*/cotizacion/{q.id:02d}.pdf'))



def test_new_quotation_validity_period(client):
    login(client, 'user1', 'pass')
    resp = client.post('/cotizaciones/nueva', data={
        'client_id': '1',
        'seller': 'User One',
        'payment_method': 'Efectivo',
        'warehouse_id': '1',
        'validity_period': '15d',
        'product_id[]': ['1'],
        'product_quantity[]': ['1'],
        'product_discount[]': ['0'],
    }, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        q = Quotation.query.order_by(Quotation.id.desc()).first()
        assert q is not None
        assert (q.valid_until - q.date).days == 15


def test_pdf_archive_folder_structure(client):
    login(client, 'user1', 'pass')

    # Cotización
    quote_resp = client.get('/cotizaciones/1/pdf')
    assert quote_resp.status_code == 200

    # Pedido + factura
    client.post('/cotizaciones/1/convertir')
    with app.app_context():
        order = Order.query.first()
        order_id = order.id
    order_resp = client.get(f'/pedidos/{order_id}/pdf')
    assert order_resp.status_code == 200

    client.get(f'/pedidos/{order_id}/facturar')
    with app.app_context():
        invoice = Invoice.query.first()
    invoice_resp = client.get(f'/facturas/{invoice.id}/pdf')
    assert invoice_resp.status_code == 200

    archive_root = Path(app.config['PDF_ARCHIVE_ROOT'])
    assert list(archive_root.glob('compa/*/cotizacion/*.pdf'))
    assert list(archive_root.glob('compa/*/pedido/*.pdf'))
    assert list(archive_root.glob('compa/*/factura/*.pdf'))
