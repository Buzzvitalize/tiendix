import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app, _archive_and_send_pdf
import weasy_pdf


def test_generate_pdf_creates_pdf_with_fpdf_renderer(tmp_path):
    output = tmp_path / 'factura.pdf'
    company = {'name': 'Comp', 'address': 'Street', 'phone': '809-555-0000'}
    client = {'name': 'Cliente', 'identifier': '001-0000000-1'}
    items = [{'product_name': 'Producto 1', 'quantity': 2, 'unit_price': 100.0, 'discount': 0.0}]

    with app.app_context():
        path = weasy_pdf.generate_pdf(
            'Factura', company, client, items,
            subtotal=200.0, itbis=36.0, total=236.0,
            output_path=output,
        )

    assert path == str(output)
    assert output.exists()
    assert output.stat().st_size > 100


class _DummyPdf:
    def __init__(self):
        self.lines = []
        self.cell_calls = 0

    def ln(self, *_args, **_kwargs):
        return None

    def set_font(self, *_args, **_kwargs):
        return None

    def set_text_color(self, *_args, **_kwargs):
        return None

    def set_fill_color(self, *_args, **_kwargs):
        return None

    def cell(self, _w, _h, txt='', **_kwargs):
        self.lines.append(txt)
        self.cell_calls += 1

    def multi_cell(self, _w, _h, txt='', **_kwargs):
        self.lines.append(txt)


def test_draw_totals_uses_real_discount_sum():
    pdf = _DummyPdf()
    weasy_pdf._draw_totals(
        pdf,
        subtotal=200.0,
        itbis=36.0,
        total=226.0,
        discount=10.0,
        note=None,
        footer=None,
    )

    assert any('Descuento: RD$ 10.00' in line for line in pdf.lines)


def test_items_table_adds_empty_rows_until_minimum():
    pdf = _DummyPdf()
    items = [
        {'code': '01', 'reference': 'A1', 'product_name': 'Prod', 'unit': 'Unidad', 'unit_price': 100.0, 'quantity': 1, 'discount': 0.0}
    ]
    weasy_pdf._draw_items_table(pdf, items, min_rows=15)

    # 8 encabezados + 15 filas * 8 columnas = 128 celdas
    assert pdf.cell_calls == 128


def test_generate_pdf_bytes_accepts_unicode_text_without_crashing():
    company = {'name': 'Comp 🚀', 'address': 'Calle Ñ', 'phone': '809-555-0000'}
    client = {'name': 'Cliente 😀', 'identifier': '001-0000000-1'}
    items = [
        {'product_name': 'Producto 💡 especial', 'quantity': 2, 'unit_price': 100.0, 'discount': 0.0}
    ]

    with app.app_context():
        payload = weasy_pdf.generate_pdf_bytes(
            'Cotización ✅', company, client, items,
            subtotal=200.0, itbis=36.0, total=236.0,
            note='Nota con emoji 🔧',
        )

    assert isinstance(payload, (bytes, bytearray))
    assert payload.startswith(b'%PDF')


def test_archive_and_send_pdf_fallbacks_to_attachment_filename(monkeypatch):
    calls = []

    def fake_send_file(payload, **kwargs):
        calls.append(kwargs)
        if 'download_name' in kwargs:
            raise TypeError('unexpected keyword argument download_name')
        assert kwargs.get('attachment_filename') == 'doc.pdf'
        return app.response_class(b'PDF', mimetype='application/pdf')

    monkeypatch.setattr('app.send_file', fake_send_file)

    with app.test_request_context('/dummy'):
        resp = _archive_and_send_pdf(
            doc_type='cotizacion',
            doc_number=1,
            pdf_data=b'%PDF-1.4 test',
            download_name='doc.pdf',
            archive=False,
        )

    assert resp.status_code == 200
    assert len(calls) == 2
