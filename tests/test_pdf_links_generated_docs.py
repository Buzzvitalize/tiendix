import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app, db
from models import CompanyInfo, User, Client, Order, Invoice


def test_order_and_invoice_pages_prefer_generated_docs_links(tmp_path):
    db_path = tmp_path / 'test.sqlite'
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['PUBLIC_DOCS_BASE_URL'] = 'https://app.ecosea.do'

    with app.app_context():
        db.drop_all()
        db.create_all()
        company = CompanyInfo(name='Eco Sea SRL', street='', sector='', province='', phone='', rnc='')
        db.session.add(company)
        db.session.flush()
        user = User(username='u_links', first_name='U', last_name='Links', role='company', company_id=company.id)
        user.set_password('pass')
        db.session.add(user)
        client = Client(name='Cliente', company_id=company.id)
        db.session.add(client)
        db.session.flush()
        order = Order(client_id=client.id, subtotal=100, itbis=18, total=118, seller='U', payment_method='Efectivo', status='Pendiente', company_id=company.id)
        db.session.add(order)
        invoice = Invoice(client_id=client.id, order_id=1, subtotal=100, itbis=18, total=118, invoice_type='Consumidor Final', status='Pendiente', company_id=company.id)
        db.session.add(invoice)
        db.session.commit()

    with app.test_client() as c:
        c.post('/login', data={'username': 'u_links', 'password': 'pass'})
        orders_html = c.get('/pedidos').get_data(as_text=True)
        invoices_html = c.get('/facturas').get_data(as_text=True)

    assert '/pedidos/1/pdf' not in orders_html
    assert '/facturas/1/pdf' not in invoices_html
