import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app, db
from models import CompanyInfo, User, Client
import weasy_pdf


def _seed_base(tmp_path):
    db_path = tmp_path / 'test.sqlite'
    app.config.from_object('config.TestingConfig')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    with app.app_context():
        db.drop_all()
        db.create_all()
        company = CompanyInfo(name='Carlos SRL', street='', sector='', province='', phone='', rnc='')
        db.session.add(company)
        db.session.flush()
        user = User(username='svcuser', first_name='Carlos', last_name='Tester', role='company', company_id=company.id)
        user.set_password('pass')
        db.session.add(user)
        client = Client(name='Cliente Servicio', company_id=company.id, email='cliente@example.com')
        db.session.add(client)
        db.session.commit()


def test_cotizaciones_page_shows_nuevo_servicio_button(tmp_path):
    _seed_base(tmp_path)
    with app.test_client() as c:
        c.post('/login', data={'username': 'svcuser', 'password': 'pass'})
        html = c.get('/cotizaciones').get_data(as_text=True)
    assert 'Nuevo Servicio' in html
    assert '/cotizaciones/nuevo-servicio' in html


def test_create_service_quotation_without_warehouse_archives_in_servicios(tmp_path, monkeypatch):
    _seed_base(tmp_path)
    captured = {}

    def _fake_archive(doc_type, doc_number, pdf_data, company_name=None, company_id=None):
        captured['doc_type'] = doc_type
        captured['doc_number'] = doc_number
        return None

    monkeypatch.setattr('app._archive_pdf_copy', _fake_archive)

    with app.test_client() as c:
        c.post('/login', data={'username': 'svcuser', 'password': 'pass'})
        resp = c.post('/cotizaciones/nuevo-servicio', data={
            'client_id': '1',
            'seller': 'Carlos Tester',
            'payment_method': 'Efectivo',
            'validity_period': '1m',
            'service_name[]': ['Biorat'],
            'service_description[]': ['funciona para ratones'],
            'service_quantity[]': ['2'],
            'service_rate[]': ['1500'],
            'note': 'Servicio especial',
        }, follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/cotizaciones')
    assert captured['doc_type'] == 'servicios'

    with app.app_context():
        from models import Quotation
        q = Quotation.query.first()
        assert q is not None
        assert q.warehouse_id is None


def test_new_service_page_loads(tmp_path):
    _seed_base(tmp_path)
    with app.test_client() as c:
        c.post('/login', data={'username': 'svcuser', 'password': 'pass'})
        resp = c.get('/cotizaciones/nuevo-servicio')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'Nuevo Servicio' in html
    assert 'Guardar Servicio' in html


def test_service_quotation_pdf_is_generated_under_servicios(tmp_path):
    _seed_base(tmp_path)
    archive_root = tmp_path / 'generated_docs'
    app.config['PDF_ARCHIVE_ROOT'] = str(archive_root)

    with app.test_client() as c:
        c.post('/login', data={'username': 'svcuser', 'password': 'pass'})
        create_resp = c.post('/cotizaciones/nuevo-servicio', data={
            'client_id': '1',
            'seller': 'Carlos Tester',
            'payment_method': 'Efectivo',
            'validity_period': '1m',
            'service_name[]': ['Instalación'],
            'service_description[]': ['Instalación de equipo'],
            'service_quantity[]': ['1'],
            'service_rate[]': ['2500'],
            'note': 'Nota de servicio',
        }, follow_redirects=False)
        assert create_resp.status_code == 302

        pdf_resp = c.get('/cotizaciones/1/pdf')

    assert pdf_resp.status_code == 200
    assert pdf_resp.headers.get('Content-Type', '').startswith('application/pdf')
    archived = list(archive_root.glob('**/servicios/*.pdf'))
    assert archived, 'Expected archived PDF under servicios folder'


def test_create_service_invoice_mode_creates_invoice_and_client(tmp_path):
    _seed_base(tmp_path)
    archive_root = tmp_path / 'generated_docs'
    app.config['PDF_ARCHIVE_ROOT'] = str(archive_root)
    with app.test_client() as c:
        c.post('/login', data={'username': 'svcuser', 'password': 'pass'})
        resp = c.post('/cotizaciones/nuevo-servicio', data={
            'create_client': '1',
            'new_client_type': 'fiscal',
            'new_client_name': 'Empresa SRL',
            'new_client_identifier': '101010101',
            'new_client_email': 'empresa@example.com',
            'seller': 'Carlos Tester',
            'payment_method': 'Efectivo',
            'validity_period': '1m',
            'document_mode': 'factura',
            'service_name[]': ['Consultoría'],
            'service_description[]': ['Proyecto mensual'],
            'service_quantity[]': ['1'],
            'service_rate[]': ['1000'],
            'service_itbis[]': ['1'],
            'note': 'Facturar este servicio',
        }, follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/facturas')

    with app.app_context():
        from models import Client, Invoice
        cli = Client.query.filter_by(name='Empresa SRL').first()
        assert cli is not None
        assert cli.is_final_consumer is False
        inv = Invoice.query.order_by(Invoice.id.desc()).first()
        assert inv is not None
        assert inv.invoice_type == 'Crédito Fiscal'
        assert inv.total > inv.subtotal

    archived = list(archive_root.glob('**/serviciofact/*.pdf'))
    assert archived, 'Expected archived service invoice PDF under serviciofact folder'


def test_service_invoice_pdf_redirects_to_serviciofact_path(tmp_path):
    _seed_base(tmp_path)
    archive_root = tmp_path / 'generated_docs'
    app.config['PDF_ARCHIVE_ROOT'] = str(archive_root)
    with app.test_client() as c:
        c.post('/login', data={'username': 'svcuser', 'password': 'pass'})
        c.post('/cotizaciones/nuevo-servicio', data={
            'client_id': '1',
            'seller': 'Carlos Tester',
            'payment_method': 'Efectivo',
            'validity_period': '1m',
            'document_mode': 'factura',
            'service_name[]': ['Instalación'],
            'service_description[]': ['Servicio técnico'],
            'service_quantity[]': ['1'],
            'service_rate[]': ['1500'],
            'service_itbis[]': ['0'],
        }, follow_redirects=False)

        pdf_resp = c.get('/facturas/1/pdf', follow_redirects=False)

    assert pdf_resp.status_code == 200
    archived_url = pdf_resp.headers.get('X-Archived-Url', '')
    assert '/generated_docs/' in archived_url or '/generated-docs/' in archived_url
    assert '/serviciofact/' in archived_url


def test_service_edit_route_updates_itbis_and_total(tmp_path):
    _seed_base(tmp_path)
    with app.test_client() as c:
        c.post('/login', data={'username': 'svcuser', 'password': 'pass'})
        c.post('/cotizaciones/nuevo-servicio', data={
            'client_id': '1',
            'seller': 'Carlos Tester',
            'payment_method': 'Efectivo',
            'validity_period': '1m',
            'service_name[]': ['Servicio Base'],
            'service_description[]': ['Sin impuesto'],
            'service_quantity[]': ['1'],
            'service_rate[]': ['1000'],
            'service_itbis[]': ['0'],
        }, follow_redirects=False)

        resp = c.post('/cotizaciones/editar-servicio/1', data={
            'client_type': 'fiscal',
            'client_name': 'Cliente Servicio',
            'client_last_name': '',
            'client_identifier': '101010101',
            'client_phone': '',
            'client_email': 'cliente@example.com',
            'seller': 'Carlos Tester',
            'payment_method': 'Efectivo',
            'bank': '',
            'validity_period': '1m',
            'note': 'Editado',
            'service_name[]': ['Servicio Base'],
            'service_description[]': ['Con impuesto'],
            'service_quantity[]': ['1'],
            'service_rate[]': ['1000'],
            'service_itbis[]': ['1'],
        }, follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/cotizaciones')

    with app.app_context():
        from models import Quotation
        q = Quotation.query.get(1)
        assert q is not None
        assert q.itbis > 0
        assert q.total > q.subtotal


def test_service_rows_use_service_edit_link(tmp_path):
    _seed_base(tmp_path)
    with app.test_client() as c:
        c.post('/login', data={'username': 'svcuser', 'password': 'pass'})
        c.post('/cotizaciones/nuevo-servicio', data={
            'client_id': '1',
            'seller': 'Carlos Tester',
            'payment_method': 'Efectivo',
            'validity_period': '1m',
            'service_name[]': ['Servicio X'],
            'service_description[]': ['Desc'],
            'service_quantity[]': ['1'],
            'service_rate[]': ['1000'],
            'service_itbis[]': ['0'],
        }, follow_redirects=False)
        html = c.get('/cotizaciones').get_data(as_text=True)
    assert '/cotizaciones/editar-servicio/1' in html




def test_service_rows_show_generate_factura_button(tmp_path):
    _seed_base(tmp_path)
    with app.test_client() as c:
        c.post('/login', data={'username': 'svcuser', 'password': 'pass'})
        c.post('/cotizaciones/nuevo-servicio', data={
            'client_id': '1',
            'seller': 'Carlos Tester',
            'payment_method': 'Efectivo',
            'validity_period': '1m',
            'service_name[]': ['Servicio X'],
            'service_description[]': ['Desc'],
            'service_quantity[]': ['1'],
            'service_rate[]': ['1000'],
            'service_discount[]': ['100'],
            'service_itbis[]': ['1'],
        }, follow_redirects=False)
        html = c.get('/cotizaciones').get_data(as_text=True)
    assert 'Generar Factura' in html


def test_generate_service_invoice_from_existing_service_quote(tmp_path):
    _seed_base(tmp_path)
    with app.test_client() as c:
        c.post('/login', data={'username': 'svcuser', 'password': 'pass'})
        c.post('/cotizaciones/nuevo-servicio', data={
            'client_id': '1',
            'seller': 'Carlos Tester',
            'payment_method': 'Efectivo',
            'validity_period': '1m',
            'service_name[]': ['Servicio X'],
            'service_description[]': ['Desc'],
            'service_quantity[]': ['1'],
            'service_rate[]': ['1000'],
            'service_discount[]': ['100'],
            'service_itbis[]': ['1'],
        }, follow_redirects=False)
        resp = c.post('/cotizaciones/1/generar-factura-servicio', data={}, follow_redirects=False)

    assert resp.status_code == 302
    assert '/facturas/1/archivo' in resp.headers['Location']

    with app.app_context():
        from models import Invoice
        inv = Invoice.query.get(1)
        assert inv is not None
        assert inv.subtotal == 900
        assert round(inv.itbis, 2) == 162
        assert round(inv.total, 2) == 1062

def test_generate_service_pdf_bytes_uses_only_user_created_rows(monkeypatch):
    original_cell = weasy_pdf._cell
    captured_texts: list[str] = []

    def tracked_cell(pdf, w, h=0, txt='', *args, **kwargs):
        captured_texts.append(str(txt))
        return original_cell(pdf, w, h, txt, *args, **kwargs)

    monkeypatch.setattr(weasy_pdf, '_cell', tracked_cell)

    company = {'name': 'Carlos SRL', 'street': '', 'phone': '', 'rnc': '', 'logo': None}
    client = {'name': 'Cliente Servicio', 'identifier': '', 'address': '', 'phone': '', 'email': ''}
    items = [
        {
            'product_name': 'Servicio A: Desc A',
            'quantity': 1,
            'unit_price': 100,
            'discount': 0,
            'has_itbis': False,
        },
        {
            'product_name': 'Servicio B: Desc B',
            'quantity': 2,
            'unit_price': 50,
            'discount': 0,
            'has_itbis': False,
        },
        {
            'product_name': 'Servicio C: Desc C',
            'quantity': 3,
            'unit_price': 25,
            'discount': 0,
            'has_itbis': True,
        },
    ]

    payload = weasy_pdf.generate_service_pdf_bytes(
        'Servicio',
        company,
        client,
        items,
        subtotal=300,
        itbis=63,
        total=363,
    )

    assert payload.startswith(b'%PDF')
    assert sum('Servicio A: Desc A' in t for t in captured_texts) == 1
    assert sum('Servicio B: Desc B' in t for t in captured_texts) == 1
    assert sum('Servicio C: Desc C' in t for t in captured_texts) == 1
    assert sum('Servicio D: Desc D' in t for t in captured_texts) == 0
