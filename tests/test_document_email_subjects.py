import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app, db
from models import CompanyInfo, User, Client, Quotation, QuotationItem, Order, OrderItem, Invoice, InvoiceItem


def test_document_email_subjects_and_body(tmp_path, monkeypatch):
    db_path = tmp_path / 'test.sqlite'
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    with app.app_context():
        db.drop_all()
        db.create_all()
        comp = CompanyInfo(name='CompX', street='', sector='', province='', phone='8090000000', rnc='123')
        db.session.add(comp)
        db.session.flush()
        user = User(username='u_mail_docs', first_name='U', last_name='One', role='company', company_id=comp.id)
        user.set_password('pass')
        db.session.add(user)
        cli = Client(name='Client', email='client@example.com', company_id=comp.id)
        db.session.add(cli)
        db.session.flush()

        now = datetime.utcnow()
        q = Quotation(client_id=cli.id, subtotal=10, itbis=0, total=10, date=now, valid_until=now + timedelta(days=15), company_id=comp.id)
        db.session.add(q)
        db.session.flush()
        db.session.add(QuotationItem(quotation_id=q.id, code='P1', product_name='Prod', unit='Unidad', unit_price=10, quantity=1, company_id=comp.id))

        o = Order(client_id=cli.id, subtotal=10, itbis=0, total=10, status='Pendiente', company_id=comp.id)
        db.session.add(o)
        db.session.flush()
        db.session.add(OrderItem(order_id=o.id, code='P1', product_name='Prod', unit='Unidad', unit_price=10, quantity=1, company_id=comp.id))

        i = Invoice(client_id=cli.id, order_id=o.id, subtotal=10, itbis=0, total=10, invoice_type='Consumidor Final', status='Pendiente', company_id=comp.id)
        db.session.add(i)
        db.session.flush()
        db.session.add(InvoiceItem(invoice_id=i.id, code='P1', product_name='Prod', unit='Unidad', unit_price=10, quantity=1, company_id=comp.id))
        db.session.commit()

    sent = []

    def fake_send(to, subject, html, attachments=None, asynchronous=True):
        sent.append((to, subject, html, attachments, asynchronous))

    monkeypatch.setattr('app.send_email', fake_send)

    with app.test_client() as c:
        c.post('/login', data={'username': 'u_mail_docs', 'password': 'pass'})
        c.post('/cotizaciones/1/enviar')
        c.post('/pedidos/1/enviar')
        c.post('/facturas/1/enviar')

    assert len(sent) == 3
    assert 'CompX - Le acaba de enviar una cotizacion #' in sent[0][1]
    assert '#1' not in sent[0][1]
    assert 'vigencia de 15 dias' in sent[0][1]
    assert 'Aqui ajustamos el link de descarga de la cotizacion solicitada' in sent[0][2]
    assert ('/generated_docs/' in sent[0][2]) or ('/cotizaciones/1/pdf' in sent[0][2])
    assert sent[0][3] is None
    assert sent[0][4] is True
    assert 'CompX - Le acaba de enviar una pedido #' in sent[1][1]
    assert '#1' not in sent[1][1]
    assert ('/generated_docs/' in sent[1][2]) or ('/pedidos/1/pdf' in sent[1][2])
    assert sent[1][3] is None
    assert sent[1][4] is True
    assert 'CompX - Le acaba de enviar una factura #' in sent[2][1]
    assert '#1' not in sent[2][1]
    assert ('/generated_docs/' in sent[2][2]) or ('/facturas/1/pdf' in sent[2][2])
    assert sent[2][3] is None
    assert sent[2][4] is True
